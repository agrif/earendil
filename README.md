# earendil

This is the beginnings of a Python irc bot framework. But that's not
the interesting part.

The interesting part is in `earendil/ircdef/messages.desc`, which is a
human-readable description of the IRC protocol. Using
```{.bash}
python3 -m earendil.ircdef
```
you can compile this description into a machine-readable JSON
description and a hyperlinked documentation website.
