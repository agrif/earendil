# earendil

<[![PyPI](https://img.shields.io/pypi/v/earendil)](https://pypi.org/project/earendil/)
[![Travis CI](https://img.shields.io/travis/com/agrif/earendil/master)](https://travis-ci.com/agrif/earendil)
[![Read the Docs](https://img.shields.io/readthedocs/earendil-irc/latest)][docs]

 [docs]: https://earendil-irc.readthedocs.io/en/latest/

This is the beginnings of a Python irc bot framework. But that's not
the interesting part.

The interesting part is in `earendil/ircdef/messages.desc`, which is a
human-readable description of the IRC protocol. Using
```{.bash}
python3 -m earendil.ircdef
```
you can compile this description into a machine-readable JSON
description and a hyperlinked documentation website.
