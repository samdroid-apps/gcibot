#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2012 Aviral Dasgupta <aviraldg@gmail.com>
# Copyright (C) 2013-15 Ignacio Rodríguez <ignacio@sugarlabs.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
import sys
import re
import requests
import datetime
from bs4 import BeautifulSoup

META = [
    "I\'m a bot written by aviraldg who inserts metadata about GCI links!",
    "Original source at: http://ur1.ca/j368e current source (forked) http://ur1.ca/j368j",
    "If you want to kick gcibot from this channel, just kick, or ask for 'ignacio' for remove it"]

SOMETHING = {
    "hi": "Hi master.",
    "bye": "Good bye!",
    "i love you": "Sorry, I'm a bot. I haven't feelings.",
    "hello": "Hello master.",
    "ping": "pong",
    "thanks": "you're welcome.",
    "thx": "you're welcome.",
    "help": "Paste a task link, and I will tell you everything about it"}

YEARS = {'2011': 7, '2012': 7, '2013': 16, '2014': 16}


class GCIBot(irc.IRCClient):
    nickname = 'gcibot'
    username = 'gcibot'
    password = 'irodriguez'

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for c in self.factory.channels:
            self.join(c)

#    def joined(self, channel):
#        self.msg(channel, META)

    def privmsg(self, user, channel, msg):
        try:
            isMaster = "!~IgnacioUy@unaffiliated/ignaciouy" in user
            user = user.split('!', 1)[0]
            isForMe = msg.startswith(
                self.nickname +
                ":") or msg.startswith(
                self.nickname +
                ",") or msg.startswith(
                self.nickname +
                " ")

            if "leave this channel " + self.nickname in msg and isMaster:
                self.msg(channel, "Yes master.")
                self.leave(channel)

            if isMaster and "join #" in msg:
                chan = msg[5:]
                self.join(chan)

            if isForMe and "about" in msg[msg.find(self.nickname):]:
                for line in META:
                    msg = "{user}, {META}".format(user=user, META=line)
                    self.msg(channel, msg)
                return

            for thing in SOMETHING:
                if isForMe and thing in msg[msg.find(self.nickname):]:
                    msg = "{user}, {msg}".format(
                        user=user,
                        msg=SOMETHING[thing])
                    self.msg(channel, msg)
                    return

            if isForMe and 'datetime' in msg:
                today = str(datetime.datetime.today())
                msg = "{user}, {date}".format(user=user, date=today)
                self.msg(channel, msg)
                return

            if isForMe and 'merry xmas' in msg or 'merry christmas' in msg:
                today = datetime.datetime.today()
                day = today.day
                month = today.month
                if day == 25 and month == 12:
                    msg = "{user}, merry christmas!".format(user=user)
                else:
                    msg = "{user}, are you serious? Christmas? pls..".format(
                        user=user)
                self.msg(channel, msg)
                return

            links = re.findall(
                'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                msg)
            for _ in links:
                isTask = re.findall("/gci/task/view/google/gci(\d+)/(\d+)", _)
                if not isTask:
                    return
                isTask = isTask[0]

                if isTask[0] not in YEARS or len(isTask) < 2 or len(
                        isTask[1]) != YEARS[
                        isTask[0]]:
                    return

                if ('google-melange.com' in _) or ('google-melange.appspot.com' in _):
                    r = requests.get(_)
                    s = BeautifulSoup(r.text)
                    A = {}
                    A['title'] = s.find('span', class_='title').string
                    A['status'] = s.find('span', class_='status').span.string
                    A['mentor'] = s.find('span', class_='mentor').span.string
                    A['remain'] = s.find(
                        'span',
                        class_='remaining').span.string
                    for _ in A.keys():
                        # IRC and Unicode don't mix very well, it seems.
                        A[_] = unicode(A[_]).encode('utf-8')

                    self.msg(channel, A['title'])
                    status = A['status']
                    if A['status'] == "Claimed" or A[
                            'status'] == "NeedsReview":
                        status = A['status'] + ' (%s)' % A['remain']
                    self.msg(channel, 'Status: ' + status)
                    self.msg(channel, 'Mentor(s): ' + A['mentor'])
        except OSError as e:
            self.describe(
                channel,
                "ERROR: '%s'. Please contact my mantainer: ignacio@sugarlabs.org" %
                str(e))

    def alterCollidedNick(self, nickname):
        return '_' + nickname + '_'


class BotFactory(protocol.ClientFactory):

    def __init__(self, channels):
        self.channels = channels

    def buildProtocol(self, addr):
        p = GCIBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    f = BotFactory(sys.argv[1:])
    reactor.connectTCP("irc.freenode.net", 6667, f)
    print "Connected to server. Channels:"
    for channel in sys.argv[1:]:
        print channel
    reactor.run()
