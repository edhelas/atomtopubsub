== About ==

AtomToPubsub is a simple Python software that parse Atom feeds and push
the entries on a XMPP Pubsub Node (http://xmpp.org/extensions/xep-0060.html)

== Installation ==

AtomToPubsub is built using Python 2.6 and use the librairies :
- feedparser
- time
- pickle
- sleekxmpp (version > 1.0, you can download and install it from here http://sleekxmpp.com/)
- sys

== Configuration ==

Rename config_default.py to config.py and set your Atom feeds and your
XMPP account configuration.

The XMPP account must be authorized to create Pubsub node on the server(s).

== Features ==

- The "key" of each feed of the configuration file will be the name of
the Pubsub node
- AtomToPubsub will try to fill the title and the description of the
Pubsub node from the title and the subtitle of the Atom node
- A cache file is created for performance issues
