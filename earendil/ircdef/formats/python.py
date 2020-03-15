# This file is generated. Make sure you are editing the right source!
# Earendil IRC Protocol Specification, version {{major_version}}.{{minor_version}}

import attr


class IrcParseError(Exception):
    pass


def decode(line, encoding='utf-8'):
    line = line.rstrip(b'\r\n').decode(encoding)
    source = None
    if line.startswith(':'):
        try:
            source, line = line.split(' ', 1)
        except ValueError:
            raise IrcParseError('no verb') from None
        source = source[1:].strip()
    last = None
    if ' :' in line:
        line, last = line.split(' :', 1)
    line = line.strip()
    if not line:
        raise IrcParseError('no verb')
    verb, *arguments = line.split()
    if last is not None:
        arguments.append(last)

    try:
        verb = int(verb)
    except ValueError:
        verb = verb.upper()

    MessageClass = MESSAGES.get(verb, UnknownMessage)
    if MessageClass is UnknownMessage:
        return UnknownMessage(source, verb, arguments)
    return MessageClass.from_arguments(source, arguments)


@attr.s(slots=True, frozen=True)
class Message:
    source = attr.ib(kw_only=True, default=None, repr=False)

    @property
    def verb(self):
        raise NotImplementedError

    @property
    def arguments(self):
        raise NotImplementedError

    def evolve(self, **kwargs):
        return attr.evolve(self, **kwargs)

    def encode(self, encoding='utf-8'):
        verb = self.verb
        if isinstance(verb, str):
            verb = verb.upper()
        else:
            verb = '{:03d}'.format(verb)

        if len(self.arguments) == 0:
            c = verb
        else:
            *args, last = self.arguments
            if ' ' in last or ':' in last:
                last = ':' + last
            c = ' '.join([verb] + args + [last])

        if self.source:
            c = ':{} {}'.format(self.source, c)
        return c.encode(encoding)


@attr.s(slots=True, frozen=True)
class UnknownMessage(Message):
    verb = attr.ib()
    arguments = attr.ib()


MESSAGES = {}

{% macro encode_arg_inner(arg, part) -%}
{%- if arg.type == 'int' -%}
str({{part}})
{%- elif arg.type == 'flag' -%}
{{arg.value|repr}}
{%- else -%}
{{part}}
{%- endif -%}
{%- endmacro %}
{% macro encode_arg(arg) -%}
{% if arg.list == 'space' -%}
' '.join({{encode_arg_inner(arg, 'v')}} for v in self.{{arg.name|snakecase}})
{%- elif arg.list == 'comma' -%}
','.join({{encode_arg_inner(arg, 'v')}} for v in self.{{arg.name|snakecase}})
{%- else -%}
{{encode_arg_inner(arg, 'self.{}'.format(arg.name|snakecase))}}
{%- endif %}
{%- endmacro %}
{% macro decode_arg_inner(arg, part) -%}
{%- if arg.type == 'int' -%}
int({{part}})
{%- elif arg.type == 'flag' -%}
True
{%- else -%}
{{part}}
{%- endif -%}
{%- endmacro %}
{% macro decode_arg(arg, i) -%}
{% if arg.list == 'space' -%}
[{{decode_arg_inner(arg, 'v')}} for v in arguments[{{i}}].split()]
{%- elif arg.list == 'comma' -%}
[{{decode_arg_inner(arg, 'v')}} for v in arguments[{{i}}].split(',')]
{%- else -%}
{{decode_arg_inner(arg, 'arguments[{}]'.format(i))}}
{%- endif %}
{%- endmacro %}
{% for msg in messages %}

@attr.s(slots=True, frozen=True)
class {{msg.name|camelcase}}(Message):
    """`{{msg.format}}`
    {% if msg.associativity == 'right' %}

    Arguments bind right-to-left.
    {% endif %}
    {% if msg.documentation %}

    {{msg.documentation}}
    {% endif %}
    {% if msg.related %}

    Related: {% for n in msg.related %}{{n|camelcase}}{% if loop.last %}.{% else%}, {% endif %}{% endfor %}
    {% endif %}

    """

    verb = {{msg.verb|repr}}
    {% set ns = namespace(after_opt=False) %}
    {% for arg in msg.arguments if arg.type != 'literal' %}
    {% if arg.optional %}
    {{arg.name|snakecase}} = attr.ib(default={% if arg.type == 'flag' %}False{% else %}None{% endif %})
    {% set ns.after_opt = True %}
    {% else %}
    {{arg.name|snakecase}} = attr.ib({% if ns.after_opt %}kw_only=True{% endif %})
    {% endif %}
    {% endfor %}

    @property
    def arguments(self):
        ret = []
        {% for arg in msg.arguments %}
        {% if arg.type == 'literal' %}
        ret.append({{arg.value|repr}})
        {% else %}
        {% if arg.optional %}
        {% if arg.type == 'flag' %}
        if self.{{arg.name|snakecase}}:
        {% else %}
        if self.{{arg.name|snakecase}} is not None:
        {% endif %}
            ret.append({{encode_arg(arg)}})
        {% else %}
        ret.append({{encode_arg(arg)}})
        {% endif %}
        {% endif %}
        {% endfor %}
        return ret

    @classmethod
    def from_arguments(cls, source, arguments):
        {% if msg.arguments %}
        {% set ns = namespace(num_req=0, cur_opt=0, num_opt=msg.arguments|length) %}
        {% for arg in msg.arguments if not arg.optional %}
        {% set ns.num_req = ns.num_req + 1 %}
        {% set ns.num_opt = ns.num_opt - 1 %}
        {% endfor %}
        num_optionals = len(arguments){% if ns.num_req %} - {{ns.num_req}}{% endif %}

        if num_optionals < 0:
            raise IrcParseError('bad arguments for {{msg.name|camelcase}}')
        i = 0

        {% for arg in msg.arguments %}
        {% if arg.type == 'literal' %}
        # literal {{arg.value|repr}}
        i += 1
        {% else %}
        {% if arg.optional %}
        v_{{arg.name|snakecase}} = {% if arg.type == 'flag' %}False{% else %}None{% endif %}

        {% if msg.associativity == 'right' %}
        if num_optionals > {{ns.num_opt - ns.cur_opt - 1}}:
        {% else %}
        if num_optionals > {{ns.cur_opt}}:
        {% endif %}
            {% set ns.cur_opt = ns.cur_opt + 1 %}
            v_{{arg.name|snakecase}} = {{decode_arg(arg, 'i')}}
            i += 1
        {% else %}
        v_{{arg.name|snakecase}} = {{decode_arg(arg, 'i')}}
        i += 1
        {% endif %}
        {% endif %}

        {% endfor %}
        {% endif %}
        return cls(
            source=source,
            {% for arg in msg.arguments if arg.type != 'literal' %}
            {{arg.name|snakecase}}=v_{{arg.name|snakecase}},
            {% endfor %}
        )


MESSAGES[{{msg.verb|repr}}] = {{msg.name|camelcase}}

{% endfor %}

if __name__ == '__main__':
    import code
    code.interact(local=locals())
