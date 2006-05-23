#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.insert(1, '.')
import os
import threading
import time
import re
from xmpp import *
from config import CONFIG
from users import CUsers
from feedchecker import JFNFeedChecker



users = CUsers()



# JFNCrawler JFNCrawler JFNCrawler JFNCrawler JFNCrawler JFNCrawler JFNCrawler

class JFNCrawler(threading.Thread):
    def __init__(self, stop=False):
        threading.Thread.__init__(self)
        self._stop = stop
        
        
    def run(self):
        fc = JFNFeedChecker()
        while not self._stop:
            feeds = users.feeds.values()
            time.sleep(60 / (len(feeds) + 1))
            for feed in feeds:
                fc.new(feed)
                fc.check()
                
                
    def stop(self):
        """Method to kill the thread"""
        self._stop = True



# JFNotifier JFNotifier JFNotifier JFNotifier JFNotifier JFNotifier JFNotifier

class JFNotifier(threading.Thread):
    def __init__(self, stop=False):
        threading.Thread.__init__(self)
        self._stop = stop
        
        
    def run(self):
        while not self._stop:
            usrs = users.values()
            time.sleep((60 * 60) / (len(usrs) + 1))
            for user in usrs:
                if XMPP.getRoster().getItem(user.jid):
                    # if user is online
                    for resource, resdata in XMPP.getRoster().getItem(user.jid)['resources'].iteritems():
                        # when
                        oa = user.getConfig('onlyavailable')
                        if not (oa == "on" and not (not resdata['show'] or resdata['show'] == 'chat')):
                            #we send all items and delete it
                            while len(user.items_pending) > 0:
                                item = user.items_pending.pop(0)
                                
                                # how to send the notification?
                                hl = user.getConfig('useheadline')
                                if not hl or hl == "on":
                                    msg = Message(
                                        to=user.jid + '/' + resource, 
                                        typ = 'headline', 
                                        subject = re.sub('<.*?>', '', item.title), 
                                        payload = [
                                            Node(
                                                tag='x', 
                                                attrs={'xmlns': 'jabber:x:oob'}, 
                                                payload=[
                                                    Node('url', payload=item.permalink), 
                                                    Node('desc', payload=re.sub('<.*?>', '', item.title))
                                                ]
                                            )
                                        ]
                                    )
                                    text = "%s\n" % item.text
                                    text += "_" * 50
                                    text += """\nFrom "%s" (%s)""" % (item.feed.title, item.feed.link)
                                    msg.setBody(re.sub('&.*?;', '', re.sub('<.*?>', '', text)))
                                    
                                else:
                                    text = """*New* item for "%s" (%s)""" % (item.feed.title, item.feed.link)
                                    text += "\n *%s*\n %s" % (re.sub('<.*?>', '', item.title), item.permalink)
                                    if item.text != "": text += "\n \n %s" % (re.sub('<.*?>', '', item.text))
                                    text += "\n "
                                    text = re.sub('&.*?;', '', re.sub('<.*?>', '', text))
                                    msg = Message(to = user.jid + '/' + resource, body = text, typ = 'chat')
                                    
                                XMPP.send(msg)
                                # wait 0.5 secs
                                time.sleep(0.5)
                            
                            user.clear_items()
                            users.save()
                
                
    def stop(self):
        """Method to kill the thread"""
        self._stop = True
        
        
    def feedNotifications(self, feedUrl):
        """Send all pending items of this feed"""
        feed = feeds[feedUrl]
        for userjid in feed.users:
            if users[userjid].feeds[feed]:
                userNotifications(userjid, "*New* items for %s (%s)" % (feed.title, feed.url))
            else:
                users[userjid].feeds[feed] = True



# Presence Presence Presence Presence Presence Presence Presence Presence

def presenceHandler(conn, pres_node):
    """Presence handler"""
    pass
    
    

# if people wants to un/subscribe this bot, we too
def subscriptionsHandler(conn, pres_node):
    """Subscription handler"""
    tipo = pres_node.getType()
    
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
        


# IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ IQ

def iqVersion(conn, iq_node):
    """IQ Version request"""
    i = Iq(
        typ='result', 
        queryNS='jabber:iq:version', 
        to=iq_node.getFrom(),
        attrs={'id': iq_node.getID()}, 
        payload=[
            Node('name', payload=['xmpppy']),
            Node('os', payload=[os.name.upper()])
        ]
    )
    conn.send(i)
    raise NodeProcessed
    
    

# Message Message Message Message Message Message Message Message Message

def messageHandler(conn, mess_node):
    """Message handler"""
    body = mess_node.getBody()
    sbody = body.split(" ")
    reply = None
    tipo = mess_node.getType()
    jid = JID(mess_node.getFrom()).getStripped()
    res = JID(mess_node.getFrom()).getResource()
    
    if body:
        """
        if jid in CONFIG['admins']:
            if body.lower() == "quit":
                crawler.stop()
                notifier.stop()
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
        
        
        """Show the help"""
        if body.startswith("help"):
            reply = """*Help*
Available commands: add, del, list, import

_ADD_ - Use this to subscribe you a new feed URL.
Example: add http://digg.com/rss/index.xml

_DEL_ - This command will remove your subsciption for a feed URL.
Example: del http://digg.com/rss/index.xml

_LIST_ - List all your feeds subscriptions.
Example: list

_IMPORT_ - This allow you to send a full OPML file with all your feeds and immediately subscribe all them.
Example: import http://my.server.com/my_feeds.opml
(currently not available)

_SET_ - Configure the system. Available options are:
 USEHEADLINE on|off - This set the method to send you each new item, by headline or not. You need a client with headline message support. Default: 'on'.
 ONLYAVAILABLE on|off - Send you notifications only when you are available/ready for chat, or when you are away too. You'll never was notified on offline. Default: 'off'.
Example: set useheadline on

_STATUS_ - Show information like you configuration, and more.
Example: status
            """
                
                
        """Add new feeds"""
        if body.startswith("add http") and "\n" not in body:
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
        if body.startswith("del http"):
            reply = "*Feed deleted*"
            feed = body[4:].strip()
            
            ok = users.del_feed(jid, feed)
            if not ok:
                reply += "\n%s isn't subscribed for %s" % (jid, feed)
            else:
                reply += "\nURL: %s\nJID: %s\n\nEnded your notifications for this feed." % (feed, jid)
                
                
        """Set ups"""
        if body.startswith("set ") and "\n" not in body:
            reply = "*Set up*"
            actions = ['useheadline', 'onlyavailable']
            modes = ['on', 'off']
            
            if len(body.split(' ')) == 3:
                action = body.split(' ')[1]
                mode = body.split(' ')[2]
                if action in actions and mode in modes:
                    ok = users.setup(jid, action, mode)
                    if ok:
                        reply += "\nChanges saved."
                    else:
                        reply += "\nError. Type 'help' for more information."
                else:
                    reply += "\nBad arguments. Type 'help' to see the options."
            else:
                reply += "\nBad format. Type 'help' to see an example."
                
            
        """List your feeds"""
        if body == "status":
            reply = "*Status*"
            reply += "\nNotifications method: " + users.notification_method(jid)
            reply += "\nNotifications when: " + users.notification_when(jid)
            reply += "\nSubscribed feeds: " + users.len_feeds(jid)
            

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
        XMPP = Client(CONFIG['jid'].getDomain(), debug=[])
        
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
        crawler = JFNCrawler()
        crawler.start()
        global notifier
        notifier = JFNotifier()
        notifier.start()
    
        while 1:
            XMPP.Process(1)
        
    except KeyboardInterrupt:
        print u"\nKeyboardInterrupt..."
        crawler.stop()
        notifier.stop()
        sys.exit(1)
        
    #except:
    #    print u"\nRestating..."
    #    os.execl(sys.executable, sys.executable, sys.argv[0])
