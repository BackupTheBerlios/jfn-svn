#!/usr/bin/python
# -*- coding: utf-8 -*-

from durus.persistent import Persistent


class CItem(Persistent):
    def __init__(self, title = '', text = '', plink = '', dte = '', feed = None):
        self.title = title
        self.text = text
        self.permalink = plink
        self.date = dte
        self.feed = feed
