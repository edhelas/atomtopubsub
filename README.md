## About AtomToPubsub

AtomToPubsub is a simple Python script that parses Atom + RSS feeds and pushes
the entries to a designated [XMPP Pubsub Node](http://xmpp.org/extensions/xep-0060.html)

## Requirements

* Python >= 3.5
* GIT Core
* PIP
* feedparser
* jsonpickle
* slixmpp
* daemonize
* apscheduler

AtomToPubsub is built using Python 3.5 and uses the libraries

## Installation

Expand the source package to a directory that you have permission to run programs. 

Edit the config.py file with your RSS feeds, and login information for your XMPP server.

Then run ./atomtopubsub.py
