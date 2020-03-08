import io

import earendil.ircdef.parser
import earendil.ircdef.template

import mkdocs
import mkdocs.plugins

import pkg_resources


class Plugin(mkdocs.plugins.BasePlugin):
    def __init__(self):
        super().__init__()
        parser = earendil.ircdef.parser.DefinitionParser()
        with pkg_resources.resource_stream(__name__, 'messages.desc') as data:
            with io.TextIOWrapper(data) as f:
                self.spec = parser.parse('messages.desc', f)

    def on_page_markdown(self, markdown, **kwargs):
        key = '{{earendil-ircdef}}'
        if key not in markdown:
            return markdown
        md = earendil.ircdef.template.render('markdown.md', self.spec)
        return markdown.replace(key, md)
