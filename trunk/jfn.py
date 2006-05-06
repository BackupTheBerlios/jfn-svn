#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
from xmpp import *


data = {
    'jid':      JID('jfn@jabberland.com/Jabber Feed Notifier'),
    'pass':     'jfnjabberlandcom',
    'server':   'jabberland.com',
    'port':     5223
}

roster = {}


def presenceHandler(conn, presence_node):
    nick=pres.getFrom().getResource()
    text=''
    if pres.getType()=='unavailable':
        if nick in roster:
            text=nick+unicode(' ÐÏËÉÎÕÌ ËÏÎÆÅÒÅÎÃÉÀ','koi8-r')
            roster.remove(nick)
    else:
        if nick not in roster:
            text=nick+unicode(' ÐÒÉÛ£Ì × ËÏÎÆÅÒÅÎÃÉÀ','koi8-r')
            roster.append(nick)
    if text: LOG(pres,nick,text)
    
    
def subscriptionsHandler(conn, presence_node):
    tipo = presence_node.getType()
    
    print ">>> SUBSCRIPTION", presence_node.getFrom(), tipo
    
    if tipo == "subscribe":
        p = Presence(to=presence_node.getFrom(),typ='subscribe')
        conn.send(p)
        p = Presence(to=presence_node.getFrom(),typ='subscribed')
        conn.send(p)
        
    elif tipo == "unsubscribe":
        p = Presence(to=presence_node.getFrom(),typ='unsubscribe')
        conn.send(p)
        p = Presence(to=presence_node.getFrom(),typ='unsubscribed')
        conn.send(p)

        #if roster.get(jid):
        #    del roster[jid]
            
    #elif tipo == "unsubscribed":
        #if roster.get(jid):
        #    del roster[jid]


def iqVersion(conn, iq_node):
    print iq_node
    
    
def messageHandler(conn,mess_node): pass


def gogogo():
    # Born a client
    global XMPP
    XMPP = Client(data['jid'].getDomain())
    
    # ...connect it to SSL port directly
    if not XMPP.connect(server = (data['server'], data['port'])):
        raise IOError('Can not connect to server :(')
            
    # ...authorize client
    if not XMPP.auth(data['jid'].getNode(), data['pass'], data['jid'].getResource()):
        raise IOError('Can not auth with server :_(')
        
    # ...register some handlers (if you will register them before auth they will be thrown away)
    XMPP.RegisterHandler('iq', iqVersion, xmlns='jabber:iq:version')
    XMPP.RegisterHandler('message', messageHandler)
    #XMPP.RegisterHandler('presence', presenceHandler)
    #XMPP.RegisterHandler('presence', subscriptionsHandler, None,          self.presence)
    #XMPP.RegisterHandler('presence', subscriptionsHandler, "unavailable", self.presence)
    XMPP.RegisterHandler('presence', subscriptionsHandler, typ="subscribe")
    XMPP.RegisterHandler('presence', subscriptionsHandler, typ="subscribed")
    XMPP.RegisterHandler('presence', subscriptionsHandler, typ="unsubscribe")
    XMPP.RegisterHandler('presence', subscriptionsHandler, typ="unsubscribed")
    
    # ...obtain roster and become available
    XMPP.sendInitPresence()

    while 1:
        XMPP.Process(1)



if __name__ == "__main__":
    try:
        gogogo()
        
    except KeyboardInterrupt:
        print u"\nKeyboardInterrupt..."
        sys.exit(1)
        
    #except:
    #    print u"\nRestating..."
    #    os.execl(sys.executable, sys.executable, sys.argv[0])
