#!/usr/bin/env python

import asyncio
import feedparser
import time
import pickle

from publishx import Publishx
import config

import logging
import importlib as imp

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
async def parse(parsed, xmpp):
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
            await xmpp.create(feed['server'], key, f.feed)

        # We check if we have some new entries
        for entry in f.entries:
            if key not in parsed or parsed[key] < entry.updated_parsed:
                print(colored('++ new entry %s' % entry.title, 'green'))
                await xmpp.publish(feed['server'], key, entry)
            else:
                print(colored('++ update entry %s' % entry.title, 'yellow'))

        # And we update the last updated date for the feed
        try:
            parsed[key] = f.feed.updated_parsed
        except AttributeError:
            print(colored('-- Parse failed for %s' % key, 'red'))

        save(parsed)

        # We distribute the parsing
        minutes = float(config.refresh_time) / len(config.feeds)
        print(colored('Parsing next feed in %.2f minutes' % minutes, 'cyan'))
        await asyncio.sleep(minutes * 60)
        asyncio.ensure_future(parse(parsed, xmpp))


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

    xmpp = Publishx(config)
    xmpp.connect()
    xmpp.process(timeout=2)
    asyncio.ensure_future(parse(load(), xmpp))
    xmpp.process()


if __name__ == '__main__':
    main()
