from termcolor import colored

import slixmpp
from slixmpp.xmlstream import ET
import slixmpp.plugins.xep_0060.stanza.pubsub as pubsub
from slixmpp.exceptions import IqError

NS_ATOM = 'http://www.w3.org/2005/Atom'
NS_JABBER_DATA = 'jabber:x:data'


class Publishx(slixmpp.ClientXMPP):
    def __init__(self, config):
        jid = config.jid
        fulljid = config.jid + "/" + config.resource
        secret = config.secret
        resource = config.resource

        slixmpp.ClientXMPP.__init__(self, fulljid, secret)

        self.add_event_handler("session_start", self.start)
        self.register_plugin('xep_0060')

    def start(self, event):
        # self.send_presence(ptype='invisible', pstatus='AtomToPubsub')
        self.get_roster()

    async def create(self, server, node, feed):
        title = description = logo = ''

        if hasattr(feed, 'title'):
            title = feed.title
            if hasattr(feed, 'subtitle'):
                description = feed.subtitle
        print(colored('>> create %s' % title, 'blue'))

        iq = self.Iq(stype="set", sto=server)
        iq['pubsub']['create']['node'] = node
        form = iq['pubsub']['configure']['form']
        form['type'] = 'submit'
        form.addField('pubsub#persist_items',
                      ftype='boolean',
                      value=1)
        form.addField('pubsub#title',
                      ftype='text-single',
                      value=title)
        form.addField('pubsub#max_items',
                      ftype='text-single',
                      value='20')
        form.addField('pubsub#type',
                      ftype='text-single',
                      value=NS_ATOM)
        form.addField('pubsub#deliver_payloads',
                      ftype='boolean',
                      value=0)
        form.addField('pubsub#description',
                      ftype='text-single',
                      value=description)

        task = iq.send(timeout=5)
        try:
            await task
        except IqError as e:
            if e.etype == 'cancel' and e.condition == 'conflict':
                print(colored('!! node %s is already created, assuming its configuration is correct' % node, 'yellow'))
                return
            raise

    async def publish(self, server, node, entry):
        iq = self.Iq(stype="set", sto=server)
        iq['pubsub']['publish']['node'] = node

        item = pubsub.Item()
        item['id'] = entry.id

        ent = ET.Element("entry")
        ent.set('xmlns', NS_ATOM)

        title = ET.SubElement(ent, "title")
        title.text = entry.title

        updated = ET.SubElement(ent, "updated")
        updated.text = entry.updated

        if hasattr(entry.content[0], 'type'):
            content = ET.SubElement(ent, "content")
            content.set('type', entry.content[0].type)
            content.text = entry.content[0].value

        if hasattr(entry, 'links'):
            for l in entry.links:
                link = ET.SubElement(ent, "link")
                link.set('href', l['href'])
                link.set('type', l['type'])
                link.set('rel', l['rel'])

        if hasattr(entry, 'authors'):
            author = ET.SubElement(ent, "author")
            name = ET.SubElement(author, "name")
            name.text = entry.authors[0].name
            if hasattr(entry.authors[0], 'href'):
                uri = ET.SubElement(author, "uri")
                uri.text = entry.authors[0].href

        item['payload'] = ent

        iq['pubsub']['publish'].append(item)

        task = iq.send(timeout=5)
        try:
            await task
        except IqError:
            raise

    def published(self):
        print('published')
