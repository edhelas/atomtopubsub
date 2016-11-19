#!/usr/bin/env python

import feedparser
import time
import pickle

import publishx
import config

import logging
import imp

log = logging.getLogger('sleekxmpp')
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

from socket import error as SocketError
from termcolor import colored, cprint

parsed = {}
connected = False
xmpp = publishx.publishx(config)

# We feed the pubsub nodes
def parse():
    imp.reload(config)

    # We parse all the feeds
    for key, feed in config.feeds.items():
        print(colored('>> parsing %s' % key , 'magenta'))
        f = feedparser.parse(feed['url'])

        if(f.bozo == 1):
            print('XML Error')
            if(hasattr(f.bozo_exception, 'getMessage')):
                print(f.bozo_exception.getMessage())
            if(hasattr(f.bozo_exception, 'getLineNumber')):
                print('at line %s' % f.bozo_exception.getLineNumber())

        if(not key in parsed):
            xmpp.create(feed['server'], key, f.feed)

        # We check if we have some new entries
        for entry in f.entries:
            if key not in parsed or parsed[key] < entry.updated_parsed:
                print(colored('++ new entry %s' % entry.title, 'green'))
                time.sleep(2)
                xmpp.publish(feed['server'], key, entry)
            else:
                print(colored('++ update entry %s' % entry.title, 'yellow'))

        # And we update the last updated date for the feed
        if(f is not None and hasattr(f, 'updated_parsed')) :
            parsed[key] = f.updated_parsed
        else:
            print(colored('-- Parse failed for %s' % key, 'red'))

        save()

        # We distribute the parsing
        print(colored('Parsing next feed in %.2f minutes' % (float(config.refresh_time)/len(config.feeds)), 'cyan'))
        time.sleep((float(config.refresh_time) * 60)/len(config.feeds))

def load():
    try:
        pkl_file = open('cache.pkl', 'rb')
        parsed = pickle.load(pkl_file)
        pkl_file.close()
        return parsed
    except IOError:
        print('Creating the cache')
        return save()

def save():
    output = open('cache.pkl', 'wb')
    pickle.dump(parsed, output)
    output.close()
    return {}

parsed = load()
connected = xmpp.connect()
xmpp.process()

if(connected) :
    while(1):
        try:
            parse()

        except KeyboardInterrupt:
            xmpp.disconnect(wait=True)
            print("Exiting...")
            break
