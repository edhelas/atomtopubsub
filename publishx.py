import logging
from termcolor import colored
import slixmpp
from slixmpp.xmlstream import ET
import slixmpp.plugins.xep_0060.stanza.pubsub as pubsub
from slixmpp.exceptions import IqError, IqTimeout, XMPPError
import re

NS_ATOM = 'http://www.w3.org/2005/Atom'
NS_JABBER_DATA = 'jabber:x:data'
IQ_TIMEOUT = 15

class Publishx(slixmpp.ClientXMPP):

    def __init__(self, config):
        jid = config.jid
        fulljid = config.jid + "/" + config.resource
        secret = config.secret
        resource = config.resource

        slixmpp.ClientXMPP.__init__(self, fulljid, secret)

        self.register_plugin('xep_0060')

    async def create(self, server, node, feed):
        title = description = logo = ''

        if hasattr(feed, 'title'):
            title = feed.title

        if hasattr(feed, 'description'):
            description = feed.description
        elif hasattr(feed, 'subtitle'):
            description = feed.subtitle

        print(colored('>> create %s' % title, 'blue'))

        iq = self.Iq(stype="set", sto=server)
        iq['pubsub']['create']['node'] = node

        form = iq['pubsub']['configure']['form']
        form['type'] = 'submit'
        form.addField('pubsub#type',
                       ftype='text-single',
                       value='urn:xmpp:pubsub-social-feed:1')
        form.addField('pubsub#persist_items',
                       ftype='boolean',
                       value=1)
        form.addField('pubsub#notify_retract',
                       ftype='boolean',
                       value=1)
        form.addField('pubsub#title',
                       ftype='text-single',
                       value=title)
        form.addField('pubsub#max_items',
                       ftype='text-single',
                       value='max')
        form.addField('pubsub#send_last_published_item',
                       ftype='text-single',
                       value='never')
        form.addField('pubsub#deliver_payloads',
                       ftype='boolean',
                       value=0)
        form.addField('pubsub#description',
                       ftype='text-single',
                       value=description)

        node_exist = False

        try:
            node_exist = await self.plugin['xep_0060'].get_node_config(server, node, timeout=IQ_TIMEOUT)
        except XMPPError as error:
            print(colored('!! Could not retrieve configure form from node %s' % node, 'yellow'))

        if not node_exist:
            task = iq.send(timeout=IQ_TIMEOUT)
            try:
                await task
            except IqError as e:
                if e.condition == 'conflict':
                    # The node already exists - get_node_config() above
                    # failed to confirm that (it can be unreliable on some
                    # servers/nodes), but this create attempt just did via
                    # the server's own conflict response. Nothing wrong
                    # here, just carry on to publish as normal.
                    print(colored('!! node %s already exists (conflict), continuing' % node, 'yellow'))
                else:
                    print('Error:', str(e))
                    raise
            except IqTimeout as e:
                print('Error:', str(e))
                raise
        else:
            print(colored('!! node %s is already created, assuming its configuration is correct' % node, 'yellow'))

    async def publish(self, server, node, entry, version):
        iq = self.Iq(stype="set", sto=server)
        iq['pubsub']['publish']['node'] = node

        item = pubsub.Item()

        # character / is causing a bug in movim. replacing : and , with - in id. It provides nicer urls.
        rex = re.compile(r'[:,\/]')
        item['id'] = rex.sub('-', str(entry.id))

        def atom(tag):
            return '{%s}%s' % (NS_ATOM, tag)

        ent = ET.Element(atom('entry'))

        title = ET.SubElement(ent, atom('title'))
        title.text = entry.title

        updated = ET.SubElement(ent, atom('updated'))
        updated.text = entry.updated

        #Content
        if version == 'atom03':
            if hasattr(entry.content[0], 'type'):
                content = ET.SubElement(ent, atom('content'))
                content.set('type', entry.content[0].type)
                content.text = entry.content[0].value
        elif version in ('rss20', 'rss10', 'atom10'):
            if hasattr(entry, "content"):
                content = ET.SubElement(ent, atom('content'))
                content.set('type', 'text/html')
                content.text = entry.content[0].value
            elif hasattr(entry, "description"):
                content = ET.SubElement(ent, atom('content'))
                content.set('type', 'text/html')
                content.text = entry.description
                print('In Description - PublishX')

        if hasattr(entry, 'links'):
            for l in entry.links:
                link = ET.SubElement(ent, atom('link'))
                if hasattr(l, 'href'):
                    link.set('href', l['href'])
                    link.set('type', l['type'])
                    link.set('rel', l['rel'])
        elif hasattr(entry, 'link'):
            link = ET.SubElement(ent, atom('link'))
            link.set('href', entry['link'])

        if hasattr(entry, 'tags'):
            for t in entry.tags:
                tag = ET.SubElement(ent, atom('category'))
                tag.set('term', t.term)

        if version == 'atom03':
            if hasattr(entry, 'authors'):
                author = ET.SubElement(ent, atom('author'))
                name = ET.SubElement(author, atom('name'))
                name.text = entry.authors[0].name

                if hasattr(entry.authors[0], 'href'):
                    uri = ET.SubElement(author, atom('uri'))
                    uri.text = entry.authors[0].href
        elif version in ('rss20', 'rss10', 'atom10'):
            if hasattr(entry, 'author'):
                author = ET.SubElement(ent, atom('author'))
                name = ET.SubElement(author, atom('name'))
                name.text = entry.author

                if hasattr(entry.author, 'href'):
                    uri = ET.SubElement(author, atom('uri'))
                    uri.text = entry.author.href

        item['payload'] = ent
        iq['pubsub']['publish'].append(item)

        task = iq.send(timeout=IQ_TIMEOUT)
        try:
            await task
            return True
        except (IqError, IqTimeout) as e:
            print(e)
            return False

    def published(self):
        print('published')
