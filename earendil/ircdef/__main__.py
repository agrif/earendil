import argparse
import io
import json
import sys

import earendil.ircdef.parser
import earendil.ircdef.template

import markdown

import pkg_resources


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
    parser = earendil.ircdef.parser.DefinitionParser()
    try:
        result = parser.parse(fname, f)
    except earendil.parser.ParseError as e:
        e.format(file=sys.stderr)
        sys.exit(1)

    if args.format == 'json':
        output = json.dumps(result, indent=2)
    elif args.format == 'markdown':
        output = earendil.ircdef.template.render('markdown.md', result)
    elif args.format == 'html':
        md = earendil.ircdef.template.render('markdown.md', result)
        output = markdown.markdown(
            md,
            extensions=['toc', 'smarty', 'attr_list'],
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
