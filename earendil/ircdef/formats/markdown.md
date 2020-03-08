# Earendil IRC Protocol Specification { #top }

*Version {{major_version}}.{{minor_version}}*

This document compiles the information in [RFC 2812][] in a
straightforward way, derived from a concise but human-editable
definition. There is also a JSON version of this document, suitable
for use in code generation.

  [RFC 2812]: https://tools.ietf.org/html/rfc2812

The messages in this document are divided into sections, corresponding
to sections of the RFC.

[TOC]

{% for section in sections %}
## {{section.title}} { #section-{{section.name}} }

{% for msg in messages if msg.section == section.name %}
### {{msg.format|e}} { #msg-{{msg.name}} }
Name: *{{msg.name}}*

{% if msg.related %}
Related: {% for rel in msg.related %}
*[{{rel}}](#msg-{{rel}})*{% if not loop.last %}, {% endif %}
{% endfor %}.
{% endif %}

{% if msg.documentation %}
{{msg.documentation | safe}}
{% endif %}

{% endfor %}
{% endfor %}
