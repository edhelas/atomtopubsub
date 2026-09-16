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
from slixmpp.exceptions import IqError, IqTimeout
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

# How long we allow a single feed fetch to take before giving up on it.
# Without this, a slow/dead feed server can hang the whole process -
# including the live XMPP connection - since feedparser's own fetch is
# a blocking call under the hood.
FEED_FETCH_TIMEOUT = 30

def setup_logging(level):
    logging.basicConfig(level=level, format='%(message)s', force=True)

    log = logging.getLogger('atomtopubsub')
    log.setLevel(level)

    # Explicitly cap every logger name slixmpp/sleekxmpp forks are known
    # to log SEND/RECV XML stanza dumps under, regardless of the root
    # logger's level.
    for name in (
        'slixmpp',
        'sleekxmpp',
        'slixmpp.xmlstream',
        'slixmpp.xmlstream.xmlstream',
        'slixmpp.stanza',
    ):
        noisy = logging.getLogger(name)
        noisy.setLevel(logging.WARNING)
        noisy.propagate = False

async def fetch_feed(key, feed):
    """Fetch and parse a single feed off the event loop thread, with a timeout.

    feedparser.parse() performs a blocking network request internally, so
    calling it directly from a coroutine would freeze the entire asyncio
    loop - and therefore the XMPP connection riding on it - for as long as
    the request takes, with no upper bound.
    """
    loop = asyncio.get_running_loop()
    try:
        f = await asyncio.wait_for(
            loop.run_in_executor(None, feedparser.parse, feed['url']),
            timeout=FEED_FETCH_TIMEOUT
        )
        return key, f
    except asyncio.TimeoutError:
        print(colored('!! Timeout fetching %s' % key, 'red'))
        return key, None
    except Exception as e:
        print(e)
        return key, None

# We feed the pubsub nodes
async def parse(parsed, xmpp):
    try:
        imp.reload(config)
    except Exception as e:
        # A bad edit to config.py (e.g. mid-deploy) must not kill the
        # whole polling loop - just keep using the previously loaded config.
        print(colored('!! Failed to reload config: %s' % e, 'red'))

    # We parse all the feeds, one after another - as soon as one feed's
    # new entries are published, we move straight on to the next, with no
    # artificial delay between them. Only once the whole list has been
    # walked do we sleep (see the end of this function), so each
    # individual feed comes back around roughly every refresh_time.
    for key, feed in config.feeds.items():
        print(colored('>> parsing %s' % key, 'magenta'))

        _, f = await fetch_feed(key, feed)

        if f is None:
            # Fetch failed or timed out - already logged in fetch_feed().
            continue

        try:
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
                except IqError as e:
                    print(colored('!! Could not create node %s: %s' % (key, e), 'red'))
                    continue

            # We check if we have some new entries
            publish_failed = False

            for entry in reversed(f.entries):
                entry_updated = getattr(entry, 'updated_parsed', None)

                if entry_updated is None:
                    # No usable date on this entry - nothing to compare
                    # against, so skip it instead of crashing on it.
                    continue

                if key not in parsed or parsed[key] < entry_updated:
                    print(colored('++ new entry %s' % entry.title, 'green'))

                    if version in ('rss20', 'rss10'):
                        if hasattr(entry, "content"):
                            soup = BeautifulSoup(entry.content[0].value, 'html.parser')
                            entry["content"][0]["value"] = soup.prettify()
                        elif hasattr(entry, "description"):
                            soup = BeautifulSoup(entry.description, 'html.parser')
                            entry.description = soup.prettify()
                            print('In description')
                    elif version == 'atom03':
                        soup = BeautifulSoup(entry.content[0].value, 'html.parser')
                        entry.content[0].type = 'xhtml'
                        comments = soup.findAll(text=lambda text: isinstance(text, Comment))
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
                            print(colored('-- XML parsing failed for %s' % entry.title, 'red'))
                            continue
                    else:
                        print(colored('>> Yet to be done', "yellow"))

                    # Publish one at a time, waiting for each IQ to
                    # actually complete before sending the next - the
                    # server rejects/times out bursts of simultaneous
                    # publishes (seen as spam protection on some
                    # deployments), so no concurrency here.
                    success = await xmpp.publish(feed['server'], key, entry, version)
                    if not success:
                        print(colored(
                            '!! Publish failed for "%s" - stopping here for %s, will retry next cycle'
                            % (entry.title, key), 'red'
                        ))
                        publish_failed = True
                        break
                else:
                    print(colored('++ update entry %s' % entry.title, 'yellow'))

            # And we update the last updated date for the feed - but only
            # if every entry made it through. If a publish failed partway
            # through, leave this alone so the whole feed (including the
            # entries that did succeed - republishing an existing item id
            # is a harmless no-op) gets retried on the next cycle instead
            # of silently marking the failed entry as "already seen".
            if not publish_failed:
                try:
                    parsed[key] = f.feed.updated_parsed
                except AttributeError:
                    print(colored('-- Parse failed for %s' % key, 'red'))

        except Exception as e:
            # Catch-all: a single malformed feed or entry must never be
            # able to take down the whole polling loop for every feed.
            print(colored('!! Unexpected error processing %s: %s' % (key, e), 'red'))
            continue

    try:
        save(parsed)
    except Exception as e:
        print(colored('!! Failed to save cache: %s' % e, 'red'))

    # Wait a full refresh cycle before starting the list over from the
    # beginning. Previously this divided refresh_time by the number of
    # feeds and slept between every single feed, which meant each feed
    # was actually re-fetched refresh_time/N minutes apart - N times more
    # often than the configured value suggests - hammering source servers
    # far harder than intended.
    print(colored('Restarting the feed list in %.2f minutes' % (config.refresh_time), 'cyan'))
    await asyncio.sleep(config.refresh_time * 60)
    asyncio.ensure_future(parse(parsed, xmpp))

def load():
    try:
        with open('cache.pkl', 'rb') as pkl_file:
            return pickle.load(pkl_file)
    except IOError:
        print('Creating the cache')
        return save({})

def save(parsed):
    with open('cache.pkl', 'wb') as output:
        pickle.dump(parsed, output)
    return {}

def clear_cache():
    try:
        remove('cache.pkl')
    except FileNotFoundError:
        pass

def sched_listener(event):
    if event.exception:
        print('The job crashed :')
    else:
        print('The job worked :')

def main():
    setup_logging(logging.INFO)

    xmpp = Publishx(config)
    xmpp.connect()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(clear_cache, 'interval', hours=16)
    scheduler.add_listener(sched_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler_started = False

    def on_session_start(_):
        nonlocal scheduler_started
        if not scheduler_started:
            scheduler.start()
            scheduler_started = True
        asyncio.ensure_future(parse(load(), xmpp))

    xmpp.add_event_handler('session_start', on_session_start)

    asyncio.get_event_loop().run_forever()

curr_dir = getcwd() #Needed so that A2SP can find the config files etc when using daemonize
daemon = Daemonize(app='atomtopubsub', pid = pid, action = main, foreground=True, chdir= curr_dir)
daemon.start()
