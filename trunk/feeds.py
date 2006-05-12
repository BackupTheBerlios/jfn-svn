#!/usr/bin/python
# -*- coding: utf-8 -*-

from durus.persistent import Persistent
from durus.persistent_set import PersistentSet
from durus.persistent_list import PersistentList
from durus.btree import BTree
from users import *
        
        
class CFeed(Persistent):
    def __init__(self, feed):
        self.feed = feed
        self.title = ''
        self.url = ''
        self.last_items = PersistentList() # last 50, for example, only hash
        self.users = PersistentSet() # CUser set


class CFeeds(Persistent):
    def __init__(self):
        self.data = BTree()
