#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.insert(1, '.')
import os
import threading
import time
import sha
import base64
import re
from xmpp import *
import feedparser
from config import CONFIG
from users import CUsers



users = CUsers()



class JFNCrawler(threading.Thread):
    def __init__(self, stp=False):
        threading.Thread.__init__(self)
        self._stp = stp
        self.nexturl = '' # next url for check
        
    def run(self):
        while not self._stp:
            time.sleep(1)
            urls = feeds.keys()
            for url in urls:
                self.checkFeed(url)
                self.feedNotifications(url)
                conndurus.commit()
                
    def stop(self):
        """Method to kill the thread"""
        self._stp = True
        
    def getNextUrl(self):
        """Return the next url for check"""
        return self.nexturl

    def checkFeed(self, feedUrl):
        """Retrieve and parse a feed""" 
        #try:
        txt = None
        feed = feeds[feedUrl]
        fp = feedparser.parse(feedUrl)

        #update feed basic data
        if fp.feed.get('title'): feed.title = fp.feed.title
        if fp.feed.get('link'): feed.url = fp.feed.link
        
        # if there are items
        if fp.get('entries') and len(fp['entries']) > 0:
            # ... we search the oldest
            fp['entries'].reverse()
            for entry in fp['entries']:
                # generate the item hash
                if entry.get('title'):
                    temp = repr(entry['title'])
                    if entry.get('link'): temp += repr(entry.link)
                    if entry.get('summary'): temp += repr(entry.summary)
                #else: temp = str(entry)
                # this have a problem: UnicodeEncodeError... 
                temphash = sha.new(temp).hexdigest()

                if not temphash in feed.last_items:
                    feed.last_items.append(temphash)
                    # ...add this item for each user
                    for userjid in feed.users:
                        ci = CItem()
                        if entry.get('title'): ci.title = entry.title
                        if entry.get('summary'): ci.text = entry.summary
                        if entry.get('link'): ci.permalink = entry.link
                        if entry.get('updated'): ci.dte = entry.updated
                        users[userjid].items_pending.append(ci)
                        
                        #delete obsolete items from users, no more than 100
                        while len(users[userjid].items_pending) > 100:
                            temp = users[userjid].items_pending[0]
                            users[userjid].items_pending.remove(temp)
                #delete obsolete hashes from feeds, no more than 50
                while len(feed.last_items) > 50:
                    temp = feed.last_items[0]
                    feed.last_items.remove(temp)

        elif fp.bozo != 0:
            txt = "*JFN Error*\n%r\n%r" % (feedUrl, fp['bozo_exception'])
            feed.errors += 1
        else:
            feed.errors = 0
            
        if txt and len(CONFIG['admins']) > 0:
            for ajid in CONFIG['admins']:
                XMPP.send(Message(to = ajid, body = txt, typ = 'chat'))
        #except:
            #pass

    def feedNotifications(self, feedUrl):
        """Send all pending items of this feed"""
        feed = feeds[feedUrl]
        for userjid in feed.users:
            if users[userjid].feeds[feed]:
                userNotifications(userjid, "*New* items for %s (%s)" % (feed.title, feed.url))
            else:
                users[userjid].feeds[feed] = True
            
            
            
def userNotifications(userjid, initialtext = None):
    """Send notification to some JID"""
    user = users[userjid]
    # if the user is conected and have pending items...
    if len(XMPP.getRoster().getResources(user.jid)) > 0 and len(user.items_pending) > 0:
        if initialtext:
            XMPP.send(Message(to = user.jid, body = initialtext, typ = 'chat'))
        user.items_pending.reverse()
        #we send all items and delete it
        while len(user.items_pending) > 0:
            item = user.items_pending.pop()
            text = "\n*%s*\n%s" % (re.sub('<.*?>', '', item.title), item.permalink)
            if item.text != "": text += "\n\n%s" % (re.sub('<.*?>', '', item.text))
            text += "\n"
            XMPP.send(Message(to = user.jid, body = text, typ = 'chat'))
            



def presenceHandler(conn, pres_node):
    """Presence handler"""
    print ">>> PRESENCE", pres_node.getFrom(), pres_node.getType(), pres_node.getShow()
    #userNotifications(JID(pres_node.getFrom()).getStripped())
    #setCustomPresenceStatus(pres_node.getFrom())
    
    
    
    
def setCustomPresenceStatus(to_jid):
    """Set up presence message status for each user"""
    jid = JID(to_jid).getStripped()
    if users.get(jid):
        p_i = len(users[jid].items_pending)
        statusmsg = "You haven't pending items."
        if p_i > 0:
            statusmsg = "You have %d item" % p_i
            if p_i > 1:
                 statusmsg += "s"
            statusmsg += " unreaded."
        p = Presence(to=to_jid, status=statusmsg)
        XMPP.send(p)
    
    

# if people wants to un/subscribe this bot, we too
def subscriptionsHandler(conn, pres_node):
    """Subscription handler"""
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
    """IQ Version request"""
    i = Iq(typ='result', queryNS='jabber:iq:version', to=iq_node.getFrom(), payload=[Node('name',payload=['xmpppy'])])
    conn.send(i)
    raise NodeProcessed
    
    
    
def messageHandler(conn, mess_node):
    """Message handler"""
    body = mess_node.getBody()
    sbody = body.split(" ")
    reply = None
    tipo = mess_node.getType()
    jid = JID(mess_node.getFrom()).getStripped()
    res = JID(mess_node.getFrom()).getResource()
    
    print ">>> MESSAGE", tipo, mess_node.getFrom(), body 

    if body:
        """if jid in CONFIG['admins']:
            if body.lower() == "quit":
                crawler.stop()
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
                     reply += "\nAlgo ha fallado... :(\n\n%r" % sys.exc_info()[0]
        """
        
        
        """Add new feeds"""
        if body.startswith("add http"):
            reply = "*Feed added*"
            feed = body[4:].strip()
            
            ok = users.add_feed(jid, feed)
            if not ok:
                reply += "\nThe feed %s is already added for %s" % (feed, jid)
            else:
                reply += "\nURL: %s\nJID: %s\n\nNow you'll start to receive the new entry items." % (feed, jid)
            
            
        """List your feeds"""
        if body == "list":
            reply = "*Feeds list*"
            if not users.get(jid):
                reply += "\nYou haven't URL feeds yet."
            else:
                for feed in users[jid].feeds.keys():
                    reply += "\n- %s (%d users)" % (feed.url, len(feed.users))


        """Delete a feed"""
        """if body.startswith("del http"):
            reply = "*Feed deleted*"
            feed = body[4:].strip()
            if users.get(jid) and users[jid].feeds.has_key(feed) and feeds.get(feed) and jid in feeds[feed].users:
                del users[jid].feeds[feed]
                feeds[feed].users.remove(jid)
                conndurus.commit()
                reply += "\nURL: %s\nJID: %s\n\nNotifications for this feed closed." % (feed, jid)
            else:
                reply += "\n%s isn't subscribed in %s" % (jid, feed)
        """


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
        global XMPP
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
        
        global crawler
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
