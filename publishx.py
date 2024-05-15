import logging
from termcolor import colored

import slixmpp
from slixmpp.xmlstream import ET
import slixmpp.plugins.xep_0060.stanza.pubsub as pubsub
from slixmpp.exceptions import IqError, IqTimeout
import re


NS_ATOM = 'http://www.w3.org/2005/Atom'
NS_JABBER_DATA = 'jabber:x:data'

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

        node_exist = await self.plugin['xep_0060'].get_node_config(server, node)
        if not node_exist:
            task = iq.send(timeout=5)
            try:
                await task
            except (IqError, IqTimeout) as e:
                print('Error:', str(e))
                raise

    async def publish(self, server, node, entry, version):
        iq = self.Iq(stype="set", sto=server)
        iq['pubsub']['publish']['node'] = node

        item = pubsub.Item()
        # character / is causing a bug in movim. replacing : and , with - in id. It provides nicer urls.
        rex = re.compile(r'[:,\/]')
        item['id'] = rex.sub('-', str(entry.id))

        ent = ET.Element("entry")
        ent.set('xmlns', NS_ATOM)

        title = ET.SubElement(ent, "title")
        title.text = entry.title

        updated = ET.SubElement(ent, "updated")
        updated.text = entry.updated
#Content
        if version == 'atom3':

            if hasattr(entry.content[0], 'type'):
                content = ET.SubElement(ent, "content")
                content.set('type', entry.content[0].type)
                content.text = entry.content[0].value
        
        elif version =='rss20' or 'rss10' or 'atom10':
            if hasattr(entry, "content"):
                content = ET.SubElement(ent, "content")
                content.set('type', 'text/html')
                content.text = entry.content[0].value
                
            elif hasattr(entry, "description"):
                content = ET.SubElement(ent,"content")
                content.set('type', 'text/html')
                content.text = entry.description
                print('In Description - PublishX')
             
#Links        
        if hasattr(entry, 'links'):
            for l in entry.links:
                link = ET.SubElement(ent, "link")
                if hasattr(l, 'href'):
                    link.set('href', l['href'])
                    link.set('type', l['type'])
                    link.set('rel', l['rel'])
                elif hasattr(entry, 'link'):
                    link.set('href', entry['link'])
 #Tags                
        if hasattr(entry, 'tags'):
            for t in entry.tags:
                tag = ET.SubElement(ent, "category")
                tag.set('term', t.term)
        
        if hasattr(entry,'category'):
            for c in entry["category"]:
                cat = ET.SubElement(ent, "category")
                cat.set('category', entry.category[0])
#Author
        if version == 'atom03':
            if hasattr(entry, 'authors'):
                author = ET.SubElement(ent, "author")
                name = ET.SubElement(author, "name")
                name.text = entry.authors[0].name
                if hasattr(entry.authors[0], 'href'):
                    uri = ET.SubElement(author, "uri")
                    uri.text = entry.authors[0].href
        
        elif version == 'rss20' or 'rss10' or 'atom10':
            if hasattr(entry, 'author'):
                author = ET.SubElement(ent, "author")
                name = ET.SubElement(ent, "author")
                name.text = entry.author
            
                if hasattr(entry.author, 'href'):
                    uri = ET.SubElement(author, "uri")
                    uri.text = entry.authors[0].href
                    
        item['payload'] = ent

        iq['pubsub']['publish'].append(item)

        task = iq.send(timeout=5)
        try:
            await task
        except (IqError, IqTimeout) as e:
            print(e)
            pass

    def published(self):
        print('published')
