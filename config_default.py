# Feed Settings

feeds = {
        
        #For ATOMFEED 1.0
        'FeedName1' : {                                          # Change this to the name of the group you want to add this feed to
            'url' : 'ATOM1.0FEEDGOESHERE',                       # Replace "ATOM1.0FEEDGOESHERE" with the URL to the Atom Feed 1.0, see the example below with golem url. 
            'server' : 'pubsubserver'                            # Change this to the pubsub servername, including the TLD (eg. pubsub.domain.tld).  See the example below
            },
        #EXAMPLE for ATOM1.0 FEED    
        # Add more feeds as you need them using this format
        #'NewGolemfeed' : {
        #    'url' : 'http://rss.golem.de/rss.php?feed=ATOM1.0 ',
        #    'server' : 'pubsub.movim.eu'
        #    },
        # Remember to add a comma ',' after every close bracket except for the last one
            
        #EXAMPLE for RSS FEED 
        # Add more feeds as you need them using this format
        #'NewTAZGermannews' : {
        #    'url' : 'https://api.movim.eu/feed/aHR0cHM6Ly93d3cudGF6LmRlLyFwNDYwODthdG9tLw==',
        #    'server' : 'news.movim.eu'
        #    },
        # Remember to add a comma ',' after every close bracket except for the last one
        
        #For RSS FEED you need to use the feedcleaner on api.movim.eu just enter the RSS Link in the box and copy it.
        'Feedname2' : {                                                     # Change this to the name of the group you want to add this feed to
            'url' : 'RSSFEEDFROMAPI.MOVIM.EUGOESHERE',                      # Replace "RSSFEEDFROMAPI.MOVIM.EUGOESHERE" with the URL you got by entering the RSS url to api.movim.eu, see example above.
            'server' : 'pubsubserver'                                       # Change this to the pubsub servername, including the TLD (eg. pubsub.domain.tld).  See the example below
            }
            
            
    }

# NB. Use Atom v0.3 feeds only

# XMPP Authentication Settings

jid         = 'user@server.tld' # XMPP UserID and domain to post the feeds as
resource    = 'atomtopubsub'    # You can change this if you want, it only tells XMPP what application posted the feeds
secret      = 'password'        # The password for the above UserID

# Refresh intervals in minutes
refresh_time = 60
# The refresh time will be split evenly over all of your feeds.
# Eg. 60 minutes across 3x feeds, will equal 1x feed will be refreshed every 20 minutes.
# Or 60 minutes across 6x feeds would equal 1x feed will be refreshed every 10 minutes.
