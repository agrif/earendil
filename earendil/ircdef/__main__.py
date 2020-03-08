import argparse
import io
import json
import sys

import earendil.ircdef.parser

import jinja2

import markdown

import pkg_resources


# custom class to turn off html processing
class EscapeHtml(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        md.preprocessors.deregister('html_block')
        md.inlinePatterns.deregister('html')


parser = argparse.ArgumentParser(
    description='Compile an IRC definition.')
parser.add_argument('-f', '--format', default='json',
                    choices=['json', 'markdown', 'html'],
                    help='output format to use')
parser.add_argument('-o', '--output',
                    help='output file name (default: stdout)')
parser.add_argument('input', nargs='?',
                    help='input description to compile')


def main(args, fname, f):
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('earendil.ircdef', 'formats'),
        autoescape=jinja2.select_autoescape(['html']),
        trim_blocks=True,
        lstrip_blocks=True,
        line_comment_prefix=None,
    )
    parser = earendil.ircdef.parser.DefinitionParser()
    try:
        result = parser.parse(fname, f)
    except earendil.parser.ParseError as e:
        e.format(file=sys.stderr)
        sys.exit(1)

    result_kwargs = {k.replace('-', '_'): v for k, v in result.items()}

    if args.format == 'json':
        output = json.dumps(result, indent=2)
    elif args.format == 'markdown':
        output = env.get_template('markdown.md').render(**result_kwargs)
    elif args.format == 'html':
        md = env.get_template('markdown.md').render(**result_kwargs)
        output = markdown.markdown(
            md,
            extensions=['toc', 'smarty', 'attr_list', EscapeHtml()],
            output_format='html5',
        )
    else:
        raise RuntimeError('unknown output format {}'.format(args.format))

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)


args = parser.parse_args()

if args.input:
    with open(args.input) as f:
        main(args, args.input, f)
else:
    with pkg_resources.resource_stream(__name__, 'messages.desc') as data:
        with io.TextIOWrapper(data) as f:
            main(args, 'messages.desc', f)
