#!/usr/bin/python
# -*- coding: utf-8 -*-

CONFIG_FILE = "config.cfg"



"""DO NOT EDIT THE NEXT LINES!!!!!!"""

from xmpp import JID

# sample config, you must edit CONFIG_FILE file
CONFIG = {
    'jid':          'jfn@server.com/Jabber Feed Notifier',
    'pass':         'secret pass',
    'server':       'server.com',
    'port':         5223,
    'durus_file':   'data/feeds.durus',
    'admins':       [] # admin jids
}

# load configuration
pf = open(CONFIG_FILE, 'r')
CONFIG.update(eval(pf.read()))
pf.close()
CONFIG['jid'] = JID(CONFIG['jid'])
