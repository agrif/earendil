import jinja2

jinja_env = jinja2.Environment(
    loader=jinja2.PackageLoader('earendil.ircdef', 'formats'),
    autoescape=jinja2.select_autoescape(['html']),
    trim_blocks=True,
    lstrip_blocks=True,
    line_comment_prefix=None,
)


def camelcase(s):
    return ''.join(w.capitalize() for w in s.split('-'))


def snakecase(s):
    n = s.replace('-', '_')
    return {
        'class': 'klass',
    }.get(n, n)


jinja_env.filters['camelcase'] = camelcase
jinja_env.filters['snakecase'] = snakecase
jinja_env.filters['repr'] = repr


def snake_case_dict(d):
    if isinstance(d, dict):
        return {k.replace('-', '_'): snake_case_dict(v) for k, v in d.items()}
    if isinstance(d, list):
        return [snake_case_dict(v) for v in d]
    return d


def render(name, spec):
    return jinja_env.get_template(name).render(**snake_case_dict(spec))
