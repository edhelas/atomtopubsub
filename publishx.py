import sys
import logging
import getpass

from optparse import OptionParser
from termcolor import colored, cprint

#from sleekxmpp.xmlstream.stanzabase import ET

import sleekxmpp
from sleekxmpp.xmlstream import ET, tostring
import sleekxmpp.plugins.xep_0060.stanza.pubsub as pubsub

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

NS_ATOM = 'http://www.w3.org/2005/Atom'
NS_JABBER_DATA = 'jabber:x:data'

class publishx(sleekxmpp.ClientXMPP):
    def __init__(self, config):
        jid        = config.jid
        fulljid    = config.jid + "/" + config.resource
        secret     = config.secret
        resource   = config.resource
        
        sleekxmpp.ClientXMPP.__init__(self, fulljid, secret)

        self.add_event_handler("session_start", self.start)
        self.register_plugin('xep_0060')

    def start(self, event):
        #self.send_presence(ptype= 'invisible', pstatus= 'AtomToPubsub')
        self.get_roster()

    def create(self, server, node, feed):
        title = description = logo = ''

        if(hasattr(feed, 'title')):
            title = feed.title
            if(hasattr(feed, 'subtitle')):
                description = feed.subtitle
        print colored('>> create %s' % title, 'blue')

        iq = self.Iq(stype="set", sto = server)
        iq['pubsub']['create']['node'] = node
        iq['pubsub']['configure']['form']['type'] = 'submit'
        iq['pubsub']['configure']['form'].addField('pubsub#persist_items',
                                            ftype = 'boolean',
                                            value = 1)
        iq['pubsub']['configure']['form'].addField('pubsub#title',
                                            ftype = 'text-single',
                                            value = title)
        iq['pubsub']['configure']['form'].addField('pubsub#max_items',
                                            ftype = 'text-single',
                                            value = '20')
        iq['pubsub']['configure']['form'].addField('pubsub#type',
                                            ftype = 'text-single',
                                            value = NS_ATOM)
        iq['pubsub']['configure']['form'].addField('pubsub#deliver_payloads',
                                            ftype = 'boolean',
                                            value = 0)
        iq['pubsub']['configure']['form'].addField('pubsub#description',
                                            ftype = 'text-single',
                                            value = description)

        try:
            print iq.send(timeout=5)
        except:
            print 'Iq Error'

    def publish(self, server, node, entry):

        iq = self.Iq(stype="set", sto = server)
        iq['pubsub']['publish']['node'] = node

        item = pubsub.Item()
        item['id'] = entry.id

        ent = ET.Element("entry")
        ent.set('xmlns', NS_ATOM)

        title = ET.SubElement(ent, "title")
        title.text = entry.title

        updated = ET.SubElement(ent, "updated")
        updated.text = entry.updated

        if(hasattr(entry.content[0], 'type')):
          content = ET.SubElement(ent, "content")
          content.set('type', entry.content[0].type)

          content.text = entry.content[0].value

        if(hasattr(entry, 'links')):
            for l in entry.links:
                link = ET.SubElement(ent, "link")
                link.set('href', l['href'])
                link.set('type', l['type'])
                link.set('rel', l['rel'])

        if(hasattr(entry, 'authors')):
            author = ET.SubElement(ent, "author")
            name   = ET.SubElement(author, "name")
            name.text = entry.authors[0].name
            if(hasattr(entry.authors[0], 'href')):
                uri    = ET.SubElement(author, "uri")
                uri.text = entry.authors[0].href

        item['payload'] = ent

        iq['pubsub']['publish'].append(item)

        try:
            print iq.send(timeout=5)
        except:
            print 'Iq Error'
    def published():
        print 'published'
