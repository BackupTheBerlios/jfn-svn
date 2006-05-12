#!/usr/bin/python
# -*- coding: utf-8 -*-

from durus.persistent import Persistent
from durus.persistent_dict import PersistentDict
from durus.persistent_list import PersistentList
from durus.btree import BTree
from feeds import *


class CUser(Persistent):
    def __init__(self, jid):
        self.jid = jid
        self.items_pending = PersistentList() # [CItem, ...]
        self.config = PersistentDict()
        self.feeds = PersistentDict() # {urlfeed: send first notification?}


class CUsers(Persistent):
    def __init__(self):
        self.data = BTree()
