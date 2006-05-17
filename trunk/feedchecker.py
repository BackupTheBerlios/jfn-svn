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
        #try:
        txt = None
        fp = feedparser.parse(_feed.url)

        #update feed basic data
        if fp.feed.get('title'): _feed.title = fp.feed.title
        if fp.feed.get('link'): _feed.url = fp.feed.link
        
        # if there are items
        if fp.get('entries') and len(fp.entries) > 0:
            # ... we search the oldest
            fp.entries.reverse()
            for entry in fp.entries:
                # clean data
                title = ''
                link = ''
                summary = ''
                updated = ''
                if entry.get('title'): title = entry.title
                if entry.get('link'): title = entry.link
                if entry.get('summary'): title = entry.summary
                if entry.get('updated'): title = entry.updated
                
                # generate the item hash
                temphash = sha.new( repr(title) + repr(link) + repr(summary) ).hexdigest()

                if not temphash in _feed.last_items:
                    _feed.last_items.append(temphash)
                    # ...add this item for each user
                    for user in _feed.users:
                        ci = CItem()
                        ci.title = title
                        ci.text = summary
                        ci.permalink = link
                        ci.dte = updated
                        user.items_pending.append(ci)
                        
                        # delete oldest items from users, no more than 100
                        while len(user.items_pending) > 100:
                            users[userjid].items_pending.pop(0)
                # delete oldest hashes from feeds, no more than 50
                while len(feed.last_items) > 50:
                    feed.last_items.pop(pop)

        #except:
        #    for ajid in CONFIG['admins']:
        #        XMPP.send(Message(to = ajid, body = txt, typ = 'chat'))
