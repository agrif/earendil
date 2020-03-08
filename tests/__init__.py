import io
import unittest

import earendil.ircdef.parser


def parse(s):
    with io.StringIO(s) as f:
        return earendil.ircdef.parser.DefinitionParser().parse('<input>', f)


class TestParse(unittest.TestCase):
    def test_parse(self):
        r = parse("""
Version: 2.4
Section: Hello, World
name: hello
Message: MSG <arg>
name: message
        """)
        self.assertEqual(r, {
            'major-version': 2,
            'minor-version': 4,
            'sections': [
                {
                    'title': 'Hello, World',
                    'name': 'hello',
                },
            ],
            'messages': [
                {
                    'name': 'message',
                    'verb': 'MSG',
                    'type': 'text',
                    'associativity': 'left',
                    'format': 'MSG <arg>',
                    'section': 'hello',
                    'arguments': [
                        {'name': 'arg', 'type': 'str'},
                    ],
                },
            ],
        })
