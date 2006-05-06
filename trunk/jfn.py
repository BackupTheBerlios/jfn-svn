#!/usr/bin/python
# -*- coding: utf-8 -*-



# Small config
CONFIG_FILE = "config.cfg"



import sys
sys.path.insert(1, '.')
import os
import threading
import time
from xmpp import *
import feedparser



# sample config, you must edit CONFIG_FILE file
CONFIG = {
    'jid':          'jfn@server.com/Jabber Feed Notifier',
    'pass':         'secret pass',
    'server':       'server.com',
    'port':         5223,
    'durus_file':   'data/feeds.durus',
    'admins':       ['your@jid']
}

# load configuration
pf = open(CONFIG_FILE, 'r')
CONFIG.update(eval(pf.read()))
pf.close()
CONFIG['jid'] = JID(CONFIG['jid'])



# durus file storage
from durus.btree import BTree
from durus.file_storage import FileStorage
from durus.connection import Connection
from durus.persistent import Persistent
from durus.persistent_set import PersistentSet
from durus.persistent_dict import PersistentDict

# we use this like a struct in C. Attributes: feed url, title, url, description, 
#    items{} as sha1(item title + description): item date
class CFeed(Persistent):
    def __init__(self, feed):
        self.feed = feed
        self.title = ''
        self.url = ''
        self.last_item_date = ()
        self.errors = 0
        self.users = PersistentSet()
      
class CUser(Persistent):
    def __init__(self, jid):
        self.jid = jid
        self.items_pending = PersistentSet()
        self.config = PersistentDict()
        self.feeds = PersistentSet()

conndurus = Connection(FileStorage(CONFIG['durus_file']))
root = conndurus.get_root()

if not root.get('feeds'):
    root['feeds'] = BTree()
    conndurus.commit()
if not root.get('users'):
    root['users'] = BTree()
    conndurus.commit()
    
feeds = root['feeds']
users = root['users']



class JFNCrawler(threading.Thread):
    def __init__(self, stp=False):
        threading.Thread.__init__(self)
        self.stp = stp
        
    def run(self):
        while not self.stp:
            time.sleep(1)
            urls = feeds.keys()
            for url in urls:
                self.checkFeed(url)
                
    def stop(self):
        self.stp = True

    def checkFeed(self, feedUrl):
        try:
            fp = feedparser.parse(feedUrl)
            if fp.bozo == 0:
                pass
        except:
            pass



def presenceHandler(conn, pres_node):
    print ">>> PRESENCE", pres_node.getFrom(), pres_node.getType(), pres_node.getShow()
    
    

# if people wants to un/subscribe this bot, we too
def subscriptionsHandler(conn, pres_node):
    tipo = pres_node.getType()
    
    print ">>> SUBSCRIPTION", pres_node.getFrom(), tipo
    
    if tipo == "subscribe":
        p = Presence(to=pres_node.getFrom(),typ='subscribe')
        conn.send(p)
        p = Presence(to=pres_node.getFrom(),typ='subscribed')
        conn.send(p)
        
    elif tipo == "unsubscribe":
        p = Presence(to=pres_node.getFrom(),typ='unsubscribe')
        conn.send(p)
        p = Presence(to=pres_node.getFrom(),typ='unsubscribed')
        conn.send(p)
        


# reply the version request
def iqVersion(conn, iq_node):
    i = Iq(typ='result', queryNS='jabber:iq:version', to=iq_node.getFrom(), payload=[Node('name',payload=['xmpppy'])])
    conn.send(i)
    raise NodeProcessed
    
    
    
def messageHandler(conn, mess_node):
    body = mess_node.getBody()
    sbody = body.split(" ")
    reply = None
    tipo = mess_node.getType()
    jid = JID(mess_node.getFrom()).getStripped()
    res = JID(mess_node.getFrom()).getResource()
    
    print ">>> MESSAGE", tipo, mess_node.getFrom(), body 

    if body:
        if jid in CONFIG['admins']:
            if body.lower() == "quit":
                sys.exit()
            
            if body.lower() == "reprroster":
                reply = "*Roster repr*"
                for j, data in XMPP.getRoster().getRawRoster().iteritems():
                    reply += u"\n%s = %r" % (j, repr(data))
    
            elif sbody[0].lower() == "get":
                reply = "*Get feed*"
                fp = feedparser.parse(sbody[1])
                try:
                    reply += "\n%s\n%s\n%s" % (fp.feed.title, fp.feed.link, fp.feed.description)
                except:
                    reply += "\nError..."
                    
            elif body.startswith("eval"):
                reply = "*EVAL*"
                try:
                    reply += "\n%r" % eval(body[5:])
                except:
                     reply += "\nAlgo ha fallado... :("
        
        """Add new feeds"""
        if body.startswith("add http"):
            reply = "*Feed added*"
            feed = body[4:].strip()
            
            if users.get(jid) and feed in users[jid].feeds and feeds.get(feed) and jid in feeds[feed].users:
                reply += "\nThe feed %s is already added for %s" % (feed, jid)
            else:
                if not users.get(jid):
                    users.add(jid, CUser(jid))
                if not feeds.get(feed):
                    feeds.add(feed, CFeed(feed))
                if not feed in users[jid].feeds:
                    users[jid].feeds.add(feed)
                if not jid in feeds[feed].users:
                    feeds[feed].users.add(jid)

                conndurus.commit()
                reply += "\nURL: %s\nJID: %s\n\nWhen I see new items I'll send you. The first time don't count." % (feed, jid)
            
            
        """List your feeds"""
        if body == "list":
            reply = "*Feeds list*"
            if not users.get(jid):
                reply += "\nYou haven't URL feeds yet."
            else:
                for feed in users[jid].feeds:
                    reply += "\n- %s (%d users)" % (feed, len(feeds[feed].users))
                    
        """Delete a feed"""
        if body.startswith("del http"):
            reply = "*Feed deleted*"
            feed = body[4:].strip()
            if users.get(jid) and feed in users[jid].feeds and feeds.get(feed) and jid in feeds[feed].users:
                users[jid].feeds.remove(feed)
                feeds[feed].users.remove(jid)
                conndurus.commit()
                reply += "\nURL: %s\nJID: %s\n\nNotifications for this feed closed." % (feed, jid)
            else:
                reply += "\n%s isn't subscribed in %s" % (jid, feed)


    """If we compose a reply to the user, we send it"""
    if reply:
        m = Message(
            to = mess_node.getFrom(),
            body = reply,
            typ = mess_node.getType())
        conn.send(m)



if __name__ == "__main__":
    try:
        # Born a client
        XMPP = Client(CONFIG['jid'].getDomain())
        
        # ...connect it to SSL port directly
        if not XMPP.connect(server = (CONFIG['server'], CONFIG['port'])):
            raise IOError('Can not connect to server :(')
                
        # ...authorize client
        if not XMPP.auth(CONFIG['jid'].getNode(), CONFIG['pass'], CONFIG['jid'].getResource()):
            raise IOError('Can not auth with server :_(')
            
        # ...register some handlers (if you will register them before auth they will be thrown away)
        XMPP.RegisterHandler('iq', iqVersion, typ='get', ns='jabber:iq:version')
        XMPP.RegisterHandler('message', messageHandler)
        XMPP.RegisterHandler('presence', presenceHandler, typ=None)
        XMPP.RegisterHandler('presence', presenceHandler, typ="unavailable")
        XMPP.RegisterHandler('presence', subscriptionsHandler, typ="subscribe")
        XMPP.RegisterHandler('presence', subscriptionsHandler, typ="subscribed")
        XMPP.RegisterHandler('presence', subscriptionsHandler, typ="unsubscribe")
        XMPP.RegisterHandler('presence', subscriptionsHandler, typ="unsubscribed")
        
        # ...obtain roster and become available
        XMPP.sendInitPresence()
        
        #crawler = JFNCrawler()
        #crawler.start()
    
        while 1:
            XMPP.Process(1)
        
    except KeyboardInterrupt:
        print u"\nKeyboardInterrupt..."
        crawler.stop()
        sys.exit(1)
        
    #except:
    #    print u"\nRestating..."
    #    os.execl(sys.executable, sys.executable, sys.argv[0])
