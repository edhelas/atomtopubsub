# Feed Settings

feeds = {
        'FeedName1' : {                                                 # Change this to the name of the group you want to add this feed to
            'url' : 'http://localhost/feedcleaner/?url=FEEDGOESHERE',   # Replace "FEEDGOESHERE" with the URL to the Atom Feed, leave the rest of of the line intact, see the example below
            'server' : 'pubsubserver'                                   # Change this to the pubsub servername, including the TLD (eg. pubsub.domain.tld).  See the example below
            },
        # Add more feeds as you need them using this format
        #'FeedName2' : {
        #    'url' : 'http://localhost/feedcleaner/?url=FEEDGOESHERE',
        #    'server' : 'pubsubserver'
        #    },
        # Remember to add a comma ',' after every close bracket except for the last one
        'Feedname3' : {
            'url' : 'http://localhost/feedcleaner/?url=http://feedurlhere/rss.xml',
            'server' : 'pubsub.movim.eu'
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
