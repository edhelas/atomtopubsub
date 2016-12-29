#!/usr/bin/env python

import feedparser
import time
import pickle

import publishx
import config

import logging
import imp

from termcolor import colored


def setup_logging(level):
    log = logging.getLogger('atomtopubsub')
    log.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)


# We feed the pubsub nodes
def parse(parsed, xmpp):
    imp.reload(config)

    # We parse all the feeds
    for key, feed in config.feeds.items():
        print(colored('>> parsing %s' % key, 'magenta'))
        f = feedparser.parse(feed['url'])

        if f.bozo == 1:
            print('XML Error')
            if(hasattr(f.bozo_exception, 'getMessage')):
                print(f.bozo_exception.getMessage())
            if(hasattr(f.bozo_exception, 'getLineNumber')):
                print('at line %s' % f.bozo_exception.getLineNumber())

        if key not in parsed:
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
        if f is not None and hasattr(f, 'updated_parsed'):
            parsed[key] = f.updated_parsed
        else:
            print(colored('-- Parse failed for %s' % key, 'red'))

        save(parsed)

        # We distribute the parsing
        minutes = float(config.refresh_time) / len(config.feeds)
        print(colored('Parsing next feed in %.2f minutes' % minutes, 'cyan'))
        time.sleep(minutes * 60)


def load():
    try:
        pkl_file = open('cache.pkl', 'rb')
        parsed = pickle.load(pkl_file)
        pkl_file.close()
        return parsed
    except IOError:
        print('Creating the cache')
        return save({})


def save(parsed):
    output = open('cache.pkl', 'wb')
    pickle.dump(parsed, output)
    output.close()
    return {}


def main():
    setup_logging(logging.INFO)

    parsed = load()

    xmpp = publishx.publishx(config)
    connected = xmpp.connect()
    xmpp.process()

    if connected:
        while True:
            try:
                parse(parsed, xmpp)

            except KeyboardInterrupt:
                xmpp.disconnect(wait=True)
                print("Exiting...")
                break


if __name__ == '__main__':
    main()
