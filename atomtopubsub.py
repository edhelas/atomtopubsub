#!/usr/bin/env python3

import asyncio
import feedparser
import pickle

from publishx import Publishx

# Add the ability to run atomtopubsub as a daemon - requires Daemonize as a dependency
from daemonize import Daemonize
from os import getcwd


pid = "/tmp/atomtopubsub.pid"

import config

import logging
import importlib as imp

from termcolor import colored
from bs4 import BeautifulSoup, Comment
from xml.etree import ElementTree

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
        version = f.version
        print('Version %s' % version)
        
        
        if f.bozo == 1:
            print('XML Error')
            if hasattr(f.bozo_exception, 'getMessage'):
                print(f.bozo_exception.getMessage())
            if hasattr(f.bozo_exception, 'getLineNumber'):
                print('at line %s' % f.bozo_exception.getLineNumber())

        if key not in parsed:
            await xmpp.create(feed['server'], key, f.feed)

        # We check if we have some new entries
        for entry in reversed(f.entries):
            if key not in parsed or parsed[key] < entry.updated_parsed:
                print(colored('++ new entry %s' % entry.title, 'green'))
                
                if version == 'rss20':
                    print(colored('In rss20','red'))
                    soup = BeautifulSoup(entry.description, 'html.parser')
                    entry.description = soup.prettify()
                    
                elif version == 'atom03':
                    # soup = BeautifulSoup(entry.content[0].value, 'lxml')
                    soup = BeautifulSoup(entry.content[0].value, 'html.parser')
                    entry.content[0].type = 'xhtml'

                    comments = soup.findAll(text=lambda text:isinstance(text, Comment))

                    for comment in comments:
                        comment.extract()

                    content_value = ('<div xmlns="http://www.w3.org/1999/xhtml">\n%s\n</div>' % soup.prettify()).splitlines()

                    try:
                        entry.content[0].value = content_value
                    except TypeError:
                        pass
                
                    try:
                        ElementTree.fromstring(''.join(entry.content[0].value))
                    except Exception as e:
                        print(e)
                        print(colored('-- XML parsing failed for %s' %  entry.title, 'red'))
                        continue
                else:
                    print(colored('>> Yet to be done', "yellow"))
                    
                await xmpp.publish(feed['server'], key, entry, version)
                
                
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
    xmpp.add_event_handler('session_start', lambda _: asyncio.ensure_future(parse(load(), xmpp)))
    xmpp.process()

curr_dir = getcwd() #Needed so that A2SP can find the config files etc when using daemonize

daemon = Daemonize(app='atomtopubsub', pid = pid, action = main, foreground=True, chdir= curr_dir)
daemon.start()

#if __name__ == '__main__':
#    main()