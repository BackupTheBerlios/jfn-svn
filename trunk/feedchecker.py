#!/usr/bin/python
# -*- coding: utf-8 -*-


import sha
import feedparser
from items import CItem


class JFNFeedChecker:
    def __init__(self, feeditem = None):
        if feeditem:
            self.new(feeditem)
        
    
    def new(self, feeditem):
        self._feed = feeditem
        
        
    def check(self):
        """Retrieve and parse a feed""" 
        try:
            txt = None
            fp = feedparser.parse(self._feed.url)
    
            #update feed basic data
            if fp.feed.get('title'): self._feed.title = fp.feed.title
            if fp.feed.get('link'): self._feed.link = fp.feed.link
            if fp.get('status') and fp.status == 301 and fp.get('href'):
                self._feed.url = fp.href
            
            # if there are items
            if fp.get('entries') and len(fp.entries) > 0:
                # ... we search the oldest
                fp.entries.reverse()
                for entry in fp.entries:
                    # clean data
                    title = ''
                    link = ''
                    text = ''
                    updated = ''
                    if entry.get('title'): title = entry.title
                    if entry.get('link'): link = entry.link
                    if entry.get('summary'): text = entry.summary
                    if entry.get('updated'): updated = entry.updated
                    
                    # generate the item hash
                    temphash = sha.new( repr(title) + repr(link) + repr(text) ).hexdigest()
    
                    if not temphash in self._feed.last_items:
                        self._feed.last_items.append(temphash)
                        # ...add this item for each user
                        for user in self._feed.users:
                            ci = CItem()
                            ci.title = title
                            ci.text = text
                            ci.permalink = link
                            ci.date = updated
                            ci.feed = self._feed
                            user.items_pending.append(ci)
                            
                            # delete oldest items from users, no more than 100
                            while len(user.items_pending) > 100:
                                user.items_pending.pop(0)
                    # delete oldest hashes from feeds, no more than 50
                    while len(self._feed.last_items) > 50:
                        self._feed.last_items.pop(pop)

        except:
            pass
        #    for ajid in CONFIG['admins']:
        #        XMPP.send(Message(to = ajid, body = txt, typ = 'chat'))
