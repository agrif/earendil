import re

import lark


message_grammar = r'''

%import common.WS
%ignore WS

// verbs only occur at beginning of string with whitespace after: \A and \b
VERBNUM : /\A[0-9]{3}\b/
VERBALPHA : /\A[A-Z]+\b/

// names only occur not surrounded by whitespace: (?<!\s) and (?!\s)
NAME : /(?<!\s)[a-z][a-z0-9]*(-[a-z][a-z0-9]*)*(?!\s)/

// literals. Try : first, fall back to bare words
REST : /:.*/
WORD.0 : /\S+/

message : verb argument*

?verb : VERBNUM | VERBALPHA

?argument : variable | literal

literal : NAME | REST | WORD

variable : "<" varspec ">" -> var_required
         | "[" varspec "]" -> var_leftassoc
         | "(" varspec ")" -> var_rightassoc

varspec : NAME varsep -> type_plain
        | "#" NAME varsep -> type_channel
        | NAME ("(" NAME ")")? ":" NAME varsep -> type_other

varsep : -> sep_none
       | "_" -> sep_space
       | "," -> sep_comma

'''


message_parser = lark.Lark(message_grammar, parser='lalr', start='message')


class ParseError(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.source = None
        self.line_number = None

    def annotate(self, source, line_number):
        self.source = source
        self.line_number = line_number

    def format(self, file=None):
        if self.source:
            print('parse error ({}:{}): {}'.format(
                self.source, self.line_number, self.args[0]), file=file)
        else:
            print('parse error: {}'.format(self.args[0], file=file))


class SectionParser:
    def __init__(self):
        self._build_location = None
        self._build_name = None
        self._build_value = None
        self._build_fields = None
        self._build_field_name = None
        self._build_field_value = None
        self._build_field_location = None

    # override these

    def push_section(self, name, value, fields):
        method = getattr(self, 'push_section_' + name.lower(), None)
        if method:
            method(value, fields)
        else:
            raise ParseError('unknown section {!r}'.format(name))

    def push_field(self, section, name, value):
        method = getattr(
            self, 'push_field_{}_{}'.format(section.lower(), name.lower()),
            None)
        if method:
            return method(value)
        else:
            raise ParseError(
                'unknown field {!r} in section {!r}'.format(name, section))

    # implementation

    def parse(self, source, fobj):
        for i, line in enumerate(fobj):
            self.push_line(source, i + 1, line)
        return self.finalize()

    def _flush_section(self):
        if self._build_name is None:
            return
        self._flush_field()

        try:
            self.push_section(self._build_name, self._build_value,
                              self._build_fields)
        except ParseError as e:
            e.annotate(*self._build_location)
            raise
        self._build_location = None
        self._build_name = None
        self._build_value = None
        self._build_fields = None

    def _flush_field(self):
        if self._build_field_name is None:
            return
        try:
            val = self.push_field(self._build_name, self._build_field_name,
                                  self._build_field_value)
        except ParseError as e:
            e.annotate(*self._build_field_location)
            raise
        self._build_fields[self._build_field_name] = val
        self._build_field_name = None
        self._build_field_value = None
        self._build_field_location = None

    def _start_section(self, source, line_number, key, val):
        self._flush_section()
        self._build_location = (source, line_number)
        self._build_name = key
        self._build_value = val
        self._build_fields = {}

    def _start_field(self, source, line_number, key, val):
        self._flush_field()

        if self._build_fields is None:
            raise ParseError('field not in section')
        if key in self._build_fields:
            raise ParseError('duplicate field {!r}'.format(key))

        self._build_field_name = key
        self._build_field_value = val
        self._build_field_location = (source, line_number)

    def _append_field(self, val):
        if self._build_field_name is None:
            raise ParseError('continuation not in field')
        if val.strip() == '.':
            self._build_field_value += '\n'
        else:
            self._build_field_value += val

    def push_line(self, source, line_number, line):
        try:
            if line.startswith(' '):
                self._append_field(line[1:])
            elif ':' in line:
                key, val = line.split(':', 1)
                if key and key[0].isupper():
                    self._start_section(source, line_number, key, val)
                else:
                    self._start_field(source, line_number, key, val)
            elif line.strip() == '':
                pass
            else:
                raise ParseError('not a section, field, or continuation')
        except ParseError as e:
            if not e.source:
                e.annotate(source, line_number)
            raise

    def finalize(self):
        self._flush_section()


class DefinitionParser(SectionParser):
    def __init__(self):
        super().__init__()
        self.version = None
        self.sections = []
        self.messages = []

    def assure_keys(self, fields, keys):
        for k in keys:
            if k not in fields:
                raise ParseError('required field {!r} missing'.format(k))

    def assure_regex(self, value, r):
        m = re.fullmatch(r, value)
        if m is None:
            raise ParseError('unexpected value {!r}'.format(value))
        return m

    def assure_name(self, value):
        value = value.strip()
        self.assure_regex(value, r'[a-z][a-z0-9]*(-[a-z][a-z0-9]*)*')
        return value

    # Version

    def push_section_version(self, value, fields):
        self.assure_keys(fields, set())
        major, minor = self.assure_regex(value.strip(), r'(\d+)\.(\d+)') \
            .groups()
        self.version = (int(major), int(minor))

    # Section

    def push_section_section(self, value, fields):
        self.assure_keys(fields, {'name'})
        fields['title'] = value.strip()
        self.sections.append(fields)

    def push_field_section_name(self, value):
        return self.assure_name(value)

    # Message

    def push_section_message(self, value, fields):
        if not self.sections:
            raise ParseError('Message must be inside a Section')

        self.assure_keys(fields, {'name'})

        value = value.strip()
        try:
            tree = message_parser.parse(value)
        except lark.exceptions.LarkError as e:
            raise ParseError(*e.args) from e

        verb = tree.children[0]
        if verb.type == 'VERBALPHA':
            fields['verb'] = str(verb)
            fields['type'] = 'text'
        elif verb.type == 'VERBNUM':
            fields['verb'] = int(verb)
            fields['type'] = 'numeric'
        else:
            raise NotImplementedError(verb.type)

        assoc = {'left', 'right'}
        arguments = []
        fields['arguments'] = arguments
        for argtree in tree.children[1:]:
            arg = {}
            arguments.append(arg)
            if argtree.data == 'literal':
                arg['type'] = 'literal'
                tok = argtree.children[0]
                if tok.type == 'REST':
                    tok = str(tok)[1:]
                else:
                    tok = str(tok)
                arg['type-argument'] = tok
            else:
                if argtree.data == 'var_leftassoc':
                    assoc.intersection_update({'left'})
                elif argtree.data == 'var_rightassoc':
                    assoc.intersection_update({'right'})

                spec = argtree.children[0]
                tyarg = None
                if spec.data == 'type_plain':
                    name, sep = spec.children
                    ty = 'str'
                elif spec.data == 'type_channel':
                    name, sep = spec.children
                    ty = 'channel'
                elif spec.data == 'type_other':
                    name, sep = spec.children[-2:]
                    ty = str(spec.children[0])
                    if len(spec.children) == 4:
                        tyarg = str(spec.children[1])

                if ty not in {'channel', 'str', 'int', 'flag', 'literal'}:
                    raise ParseError('unknown argument type {!r}'.format(ty))
                if tyarg is not None and ty not in {'flag', 'literal'}:
                    raise ParseError(
                        'type {!r} cannot have argument'.format(ty))

                arg['name'] = str(name)
                innerarg = dict(type=str(ty))
                if tyarg is not None:
                    innerarg['type-argument'] = tyarg
                if sep.data == 'sep_none':
                    pass
                elif sep.data == 'sep_space':
                    innerarg = dict(inner=innerarg)
                    innerarg['type'] = 'space-list'
                elif sep.data == 'sep_comma':
                    innerarg = dict(inner=innerarg)
                    innerarg['type'] = 'comma-list'
                else:
                    raise RuntimeError(sep.data)

                if argtree.data == 'var_required':
                    arg.update(innerarg)
                else:
                    arg['type'] = 'optional'
                    arg['inner'] = innerarg

        if not assoc:
            raise ParseError('mixed associativity in message')
        fields['associativity'] = list(sorted(assoc))[0]
        fields['format'] = value
        fields['section'] = self.sections[-1]['name']

        self.messages.append(fields)

    def push_field_message_name(self, value):
        return self.assure_name(value)

    def push_field_message_related(self, value):
        verbs = [v.strip() for v in value.split(',')]
        return verbs

    def push_field_message_documentation(self, value):
        # FIXME markdown render here??
        return value.strip()

    # final steps

    def finalize(self):
        super().finalize()

        if self.version is None:
            raise ParseError('version never specified')

        for msg in self.messages:
            resolved = []
            for r in msg.get('related', []):
                try:
                    verb = int(r)
                except ValueError:
                    verb = r
                for other in self.messages:
                    if other['verb'] == verb:
                        resolved.append(other['name'])
                        break
                else:
                    raise ParseError(
                        'could not resolve related {!r} for {!r}'.format(
                            r, msg['name']))
            if resolved:
                msg['related'] = resolved

        return {
            'major-version': self.version[0],
            'minor-version': self.version[1],
            'sections': self.sections,
            'messages': self.messages,
        }
