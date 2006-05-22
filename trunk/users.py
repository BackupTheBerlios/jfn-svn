#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import CONFIG
from durus.file_storage import FileStorage
from durus.connection import Connection
from durus.persistent import Persistent
from durus.persistent_dict import PersistentDict
from durus.persistent_list import PersistentList
from durus.persistent_set import PersistentSet
from feeds import CFeeds, CFeed


class CUser(Persistent):
    def __init__(self, jid):
        self.jid = jid
        self.items_pending = PersistentList() # [CItem, ...]
        self.config = PersistentDict()
        self.feeds = PersistentDict() # {CFeed: send first notification?}
        
        
    def __len__(self):
        return len(self.feeds)
            
        
    def subs_feed(self, feeditem, sendFirstNoti=False):
        """Add a feed item in 'feeds' dict."""
        if not self.has_feed(feeditem):
            self.feeds[feeditem] = sendFirstNoti
            return True
        return False
        
        
    def unsubs_feed(self, feeditem):
        """Delete a feed item from 'feeds' dict."""
        if self.has_feed(feeditem):
            del self.feeds[feeditem]
            return True
        return False
            
            
    def has_feed(self, feeditem):
        """Search the url feed in 'feeds' dict"""
        for x in self.feeds.keys():
            if x.url == feeditem.url:
                return True
        return False
        
        
    def enableNotifications(self, feeditem):
        self.feeds[feeditem] = True
        
        
    def getNotification(self, feeditem):
        return self.feeds[feeditem]
        
    
    def clear_items(self):
        self.items_pending = PersistentList()
        
        
    def setup(self, action, mode):
        self.config[action] = mode
        return True
        
        
    def getConfig(self, key):
        return self.config.get(key)


class CUsers(Persistent):
    def __init__(self):
        # durus file storage
        self.conndurus = Connection(FileStorage(CONFIG['durus_file']))
        root = self.conndurus.get_root()
        
        if not root.get('users'):
            root['users'] = PersistentDict() # {user jid: CUser}
        if not root.get('feeds'):
            root['feeds'] = CFeeds()
        self.data = root['users']
        self.feeds = root['feeds']
        self.save()
        
        
    def save(self):
        self.conndurus.commit()
        
        
    def __getitem__(self, key):
        return self.data.get(key)
        
        
    def __len__(self):
        return len(self.data)
    
    
    def add_feed(self, jid, feed=None):
        """Add an user if not exists and subscribe the feed url, if not exists.
        """
        
        fn = True # first notification?

        if not self.data.get(jid):
            self.data[jid] = CUser(jid)
        if not self.feeds.get(feed) and feed:
            self.feeds[feed] = CFeed(feed)
            fn = False

        if feed:
            oku = self.data[jid].subs_feed(self.feeds[feed], fn)
            okf = self.feeds[feed].add_user(self.data[jid])
            
        self.save()
        
        if feed:
            return oku and okf
        else:
            return oku
        
    
    def del_feed(self, jid, feed):
        """Delete an user subscription."""

        tempfeed = self.feeds.get(feed)
        tempuser = self.data.get(jid)
        
        if tempuser: oku = self.data[jid].unsubs_feed(tempfeed)
        else: oku = False
        if tempfeed: okf = self.feeds[feed].del_user(tempuser)
        else: okf = False
            
        self.save()
        
        return oku and okf
        
        
    def notification_method(self, jid):
        """Return 'how the user will receive the notifications'"""
        tempuser = self.data.get(jid)
        if tempuser:
            hl = tempuser.getConfig('useheadline')
            if not hl or hl == "on":
                return "by headlines"
            return "by chat message"
        else:
            return "-"
        
    def notification_when(self, jid):
        """Return 'when the user wants to receive notifications'"""
        tempuser = self.data.get(jid)
        if tempuser:
            oa = tempuser.getConfig('onlyavailable')
            if not oa or oa == "off":
                return "always"
            return "available only, or ready for chat"
        else:
            return "-"
        
    def len_feeds(self, jid):
        tempuser = self.data.get(jid)
        if tempuser:
            return str(len(tempuser))
        else:
            return "0"
            
            
    def setup(self, jid, action, mode):
        tempuser = self.data.get(jid)
        if not tempuser:
            tempuser = CUser(jid)
            self.data[jid] = tempuser
        
        tempuser.setup(action, mode)
        return True
        
    
    def get(self, key):
        return self.data.get(key)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()
