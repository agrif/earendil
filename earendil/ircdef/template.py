import jinja2

jinja_env = jinja2.Environment(
    loader=jinja2.PackageLoader('earendil.ircdef', 'formats'),
    autoescape=jinja2.select_autoescape(['html']),
    trim_blocks=True,
    lstrip_blocks=True,
    line_comment_prefix=None,
)


def render(name, spec):
    spec_kwargs = {k.replace('-', '_'): v for k, v in spec.items()}
    return jinja_env.get_template(name).render(**spec_kwargs)
