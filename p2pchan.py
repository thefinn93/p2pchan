#!/usr/bin/env python
import sys
import os
import sqlite3
import ConfigParser
import commands
import random

from funcs import *
from kaishi import kaishi


class P2PChan(object):
    def __init__(self, host, kaishi_port, postsperpage, config):
        self.config = config
        self.kaishi = kaishi(host)
        self.kaishi.peerid = self.kaishi.host + ':' + str(kaishi_port)
        self.kaishi.handleIncomingData = self.handleIncomingData
        self.kaishi.handleAddedPeer = self.handleAddedPeer
        self.kaishi.handlePeerNickname = self.handlePeerNickname
        self.kaishi.handleDroppedPeer = self.handleDroppedPeer

        self.postsperpage = postsperpage

        self.kaishi.start()

    def makeToken(self):
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        tokenlength = random.randint(10, 30)
        token = ""
        for i in range(0, tokenlength):
            token += random.choice(chars)
        self.tokens.append(token)
        return token

  #============================================================================
  # kaishi hooks
    def handleIncomingData(self, peerid, identifier, uid, message):
        conn = sqlite3.connect(localFile('posts.db'))
        if identifier == 'POST':
            post = decodePostData(message)
            if not self.havePostWithGUID(post[0]):
                logMessage("New Post!\n" + message)
                c = conn.cursor()
                c.execute('select count(*) from posts where timestamp = \'' + post[2] + '\' and file = \'' + post[8] + '\'')
                for row in c:
                    if row[0] == 0:
                        c.execute("insert into posts values ('" + "', '".join(post) + "')")
                        conn.commit()
                        if post[1] != "" and post[5].lower() != 'sage':
                            c.execute('select * from posts where guid = \'' + post[1] + '\' limit 1')
                            for row in c:
                                if row[3] < post[3]:
                                    c.execute("update posts set bumped = '" + str(post[3]) + "' where guid = '" + post[1] + "'")
                                    conn.commit()
        elif identifier == 'THREAD':
            if self.havePostWithGUID(message):
                logMessage("New Thread!\n" + message)
                c = conn.cursor()
                c.execute('select * from posts where guid = \'' + message.replace("'", '&#39;') + '\' limit 1')
                for post in c:
                    self.kaishi.sendData('POST', encodePostData(post), to=peerid, bounce=False)
                c.execute('select * from posts where parent = \'' + message.replace("'", '&#39;') + '\'')
                for post in c:
                    self.kaishi.sendData('POST', encodePostData(post), to=peerid, bounce=False)
        elif identifier == 'THREADS':
            i = 0
            c = conn.cursor()
            c2 = conn.cursor()
            c.execute('select * from posts where parent = \'\' order by bumped desc limit 50')
            for post in c:
                logMessage("Sending posts to " + niceip(self, peerid))
                self.kaishi.sendData('POST', encodePostData(post), to=peerid, bounce=False)
                c2.execute('select * from posts where parent = \'' + post[0] + '\'')
                for reply in c2:
                    self.kaishi.sendData('POST', encodePostData(reply), to=peerid, bounce=False)
                    i += 1
                i += 1
            logMessage(niceip(self, peerid) + ' has requested to receive the latest threads.  Sent ' + str(i) + ' posts.')
        conn.close

    def handleAddedPeer(self, peerid):
        if peerid != self.kaishi.peerid:
            logMessage(niceip(self, peerid) + " has joined the network. ")

    def handlePeerNickname(self, peerid, nick):
        pass

    def handleDroppedPeer(self, peerid):
        logMessage(niceip(self, peerid) + " has dropped from the network. ")
  #==============================================================================

    def havePostWithGUID(self, guid):
        conn = sqlite3.connect(localFile('posts.db'))
        c = conn.cursor()
        c.execute('select count(*) from posts where guid = \'' + guid.replace("'", '&#39;') + '\'')
        for row in c:
            if row[0] > 0:
                conn.close()
                return True
        conn.close()
        return False

    def terminate(self, dummy=None):
        logMessage('Goodbye.')
        self.kaishi.gracefulExit()

if __name__ == '__main__':
    logMessage('Initializing...')

    config = ConfigParser.RawConfigParser()
    config.read(localFile('p2pchan.ini'))

    debug = False
    kaishi_port = 44545
    web_port = 8080
    stylesheet = 'futaba'
    postsperpage = 10

    try:
        if config.get("p2pchan", "debug").lower() == 'true':
            debug = True
    except:
        pass
    try:
        kaishi_port = config.get("p2pchan", "kaishi port")
    except:
        pass
    try:
        web_port = config.get("p2pchan", "web port")
    except:
        pass
    try:
        stylesheet = config.get("p2pchan", "stylesheet")
    except:
        pass
    try:
        postsperpage = config.get("p2pchan", "posts per page")
    except:
        pass
    if len(sys.argv) == 2:
        host = sys.argv[1]
    elif config.has_option("p2pchan", "ip"):
        host = config.get("p2pchan", "ip")
    else:
        host = raw_input("this is kinda derpy, but I need your CJDNS ip: ")

    #config = ConfigParser.ConfigParser()
    if not config.has_section("p2pchan"):
        config.add_section('p2pchan')
    config.set('p2pchan', 'kaishi port', kaishi_port)
    config.set('p2pchan', 'web port', web_port)
    config.set('p2pchan', 'stylesheet', stylesheet)
    config.set('p2pchan', 'posts per page', postsperpage)
    config.set('p2pchan', 'ip', host)

    if debug:
        config.set('p2pchan', 'debug', 'true')

    f = open(localFile('p2pchan.ini'), 'w')
    config.write(f)
    f.close()

    conn = sqlite3.connect(localFile('posts.db'))
    initializeDB(conn)

    p2pchan = P2PChan(host, int(kaishi_port), postsperpage, config)
    p2pchan.kaishi.debug = debug

    try:
        if os.name == "nt":
            import win32api
            win32api.SetConsoleCtrlHandler(p2pchan.terminate, True)
        else:
            import signal
            signal.signal(signal.SIGTERM, p2pchan.terminate)
    except:
        pass

    logMessage('Now available on the P2PChan network.')
    logMessage('Please ensure UDP port ' + str(kaishi_port) + ' is open.')
    p2pchan.kaishi.debugMessage("Requesting threads...")
    p2pchan.kaishi.sendData('THREADS', "")

    if not os.path.isfile(localFile('nodemode')):
        from twisted.web import static, server, resource
        from twisted.internet import reactor
        from p2pweb import P2PChanWeb

        if len(p2pchan.kaishi.peers) != 1:
            logMessage('There are currently ' + str(len(p2pchan.kaishi.peers)) + ' other users online.')
        else:
            logMessage('There is currently ' + str(len(p2pchan.kaishi.peers)) + ' other user online.')
        logMessage('Visit http://127.0.0.1:' + str(web_port) + ' to begin.')

        root = resource.Resource()
        root.putChild("", P2PChanWeb(p2pchan, stylesheet))
        root.putChild("manage", P2PChanWeb(p2pchan, stylesheet))
        root.putChild("peerlist", P2PChanWeb(p2pchan, stylesheet))
        root.putChild("cactus", P2PChanWeb(p2pchan,stylesheet))
        root.putChild("css", static.File(localFile('css')))
        root.putChild("content", static.File(localFile('content')))

        site = server.Site(root)

        try:
            reactor.listenTCP(int(web_port), site)
        except:
            logMessage("FATAL ERROR: Unable to bind the web server to port " + str(web_port) + ".  Is it already in use?")
            raw_input('')
            sys.exit()

        reactor.run()
    else:
        print '----------------------------------------'
        logMessage('Notice: Running in node mode.')
        logMessage('Notice: No web server has been started.')
        print '----------------------------------------'

    try:
        while True:
            raw_input('')
    except:
        pass
