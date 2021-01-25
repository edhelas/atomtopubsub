#!/usr/bin/env python3

import asyncio
from asyncio.exceptions import IncompleteReadError
from http.client import IncompleteRead
from urllib import error

import feedparser
import pickle

#apscheduler
from apscheduler import schedulers
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import BaseScheduler, STATE_STOPPED
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
#cache cleanup
from os import remove

from slixmpp.exceptions import IqTimeout

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
        try:
            f = feedparser.parse(feed['url'])
        except (IncompleteReadError, IncompleteRead, error.URLError) as e:
            print(e)
            continue    
        version = f.version
        print('Version %s' % version)
        
        
        if f.bozo == 1:
            print('XML Error')
            if hasattr(f.bozo_exception, 'getMessage'):
                print(f.bozo_exception.getMessage())
            if hasattr(f.bozo_exception, 'getLineNumber'):
                print('at line %s' % f.bozo_exception.getLineNumber())
        
        if key not in parsed:
            try:
                await xmpp.create(feed['server'], key, f.feed)
            except IqTimeout:
                print('IqTimeout Error')
                continue
        # We check if we have some new entries
        for entry in reversed(f.entries):
            if key not in parsed or parsed[key] < entry.updated_parsed:
                print(colored('++ new entry %s' % entry.title, 'green'))
                
                if version == 'rss20' or 'rss10':
                    if hasattr(entry, "content"):
                        soup = BeautifulSoup(entry.content[0].value)
                        entry["content"][0]["value"] = soup.prettify()
                        

                    elif hasattr(entry, "description"):
                        soup = BeautifulSoup(entry.description)
                        entry.description = soup.prettify()
                        print('In description')

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
    
    scheduler = AsyncIOScheduler()
    if not scheduler.running:
        try:
            scheduler.add_job(clear_cache(), 'interval', hours=16)
            scheduler.start()
            scheduler.add_listener(sched_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        except:
            pass

    output = open('cache.pkl', 'wb')
    pickle.dump(parsed, output)
    output.close()
    
    
    return {}

def clear_cache():
    remove('cache.pkl')

def sched_listener(event):
    if event.exception:
        print('The job crashed :')
    else:
        print('The job worked :')

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
#    main()scheduler = AsyncIOScheduler()