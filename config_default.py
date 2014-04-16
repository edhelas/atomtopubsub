# The feeds, /!\ Put Atom feeds only
feeds = {
        'YIFY' : {
            'url' : 'http://localhost/feedcleaner/?url=http://yify-torrents.com/rss',
            'server' : 'pubsub.movim.eu'
            },
            
        'LEquipe' : {
            'url' : 'http://localhost/feedcleaner/?url=http://www.lequipe.fr/rss/actu_rss.xml',
            'server' : 'sport.mov.im'
            },
        'SportingNews' : {
            'url' : 'http://localhost/feedcleaner/?url=http://www.sportingnews.com/rss',
            'server' : 'sport.mov.im'
            },

        'OuestFrance' : {
            'url' : 'http://localhost/feedcleaner/?url=http://www.ouest-france.fr/rss.xml',
            'server' : 'news.mov.im'
            }
    }

# XMPP 
jid         = 'user@server.tld'
resource    = 'atomtopubsub'
secret      = 'password'

# Refresh intervals in minutes
refresh_time = 15
