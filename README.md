## About AtomToPubsub

AtomToPubsub is a simple Python script that parses Atom + RSS feeds and pushes
the entries to a designated [XMPP Pubsub Node](http://xmpp.org/extensions/xep-0060.html)

## Requirements

* Python >= 3.5
* GIT Core
* PIP
* apscheduler
* daemonize
* feedparser
* jsonpickle
* slixmpp
* termcolor

AtomToPubsub is built using Python 3.5 and uses the libraries

On Debian based distributions

    apt install python3-apscheduler python3-feedparser python3-jsonpickle python3-slixmpp python3-daemonize python3-termcolor

## Installation

Expand the source package to a directory that you have permission to run programs.

Edit the config.py file with your RSS feeds, and login information for your XMPP server.

Then run ./atomtopubsub.py
