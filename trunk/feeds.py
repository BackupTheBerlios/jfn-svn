#!/usr/bin/python
# -*- coding: utf-8 -*-

from durus.persistent import Persistent
from durus.persistent_dict import PersistentDict
from durus.persistent_list import PersistentList
from durus.persistent_set import PersistentSet
        
        
class CFeed(Persistent):
    def __init__(self, urlfeed):
        self.url = urlfeed
        self.title = ''
        self.link = ''
        self.last_items = PersistentList() # last 50, for example, only hash
        self.users = PersistentSet() # CUser set
        
        
    def add_user(self, useritem):
        if not self.has_jid(useritem):
            self.users.add(useritem)
            return True
        return False
            
            
    def has_jid(self, useritem):
        """Search the user jid in 'users' set"""
        for x in self.users:
            if x.jid == useritem.jid:
                return True
        return False


class CFeeds(Persistent):
    def __init__(self):
        self.data = PersistentDict() # {url feed: CFeed}
        
        
    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, item):
        self.data[key] = item

    def __delitem__(self, key):
        self._p_note_change()
        del self.data[key]

    def get(self, key):
        return self.data.get(key)

    def keys(self):
        return self.data.keys()
