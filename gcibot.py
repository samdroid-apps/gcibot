# Copyright (C) 2012 Aviral Dasgupta <aviraldg@gmail.com>
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
from bs4 import BeautifulSoup

META = '''I\'m a bot written by aviraldg who inserts metadata about GCI links!
Source at: https://github.com/aviraldg/gcibot.
If you want to kick gcibot from this channel, just kick, or ask for 'ignacio' for remove it'''


class GCIBot(irc.IRCClient):
    nickname = '_gcibot_'
    username = 'gcibot'
    password = 'onepassword...'

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
        isMaster = "!~IgnacioUy@unaffiliated/ignaciouy" in user
        user = user.split('!', 1)[0]
        isForMe = msg.startswith(
            self.nickname +
            ":") or msg.startswith(
            self.nickname +
            ",") or msg.startswith(
            self.nickname +
            " ")

        if "leave this channel gcibot" in msg and isMaster:
            self.msg(channel, "Yes master.")
            self.leave(channel)

        if isMaster and "join #" in msg:
            chan = msg[5:]
            print chan, msg
            self.join(chan)

        if isForMe and "ping" in msg[msg.find(self.nickname):]:
            msg = "{user}: pong".format(user=user)
            self.msg(channel, msg)
            return

        if isForMe and "about" in msg[msg.find(self.nickname):]:
            msg = "{user}: {META}".format(user=user, META=META)
            self.msg(channel, msg)
            return

        if isForMe and "hi" in msg[msg.find(self.nickname):]:
            msg = "{user}: Who are you, and how you know me?".format(user=user)
            self.msg(channel, msg)
            return

        links = re.findall(
            'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            msg)
        for _ in links:
            if ('google-melange.com' in _) or ('google-melange.appspot.com' in _):
                r = requests.get(_)
                s = BeautifulSoup(r.text)
                A = {}
                A['title'] = s.find('span', class_='title').string
                A['status'] = s.find('span', class_='status').span.string
                A['mentor'] = s.find('span', class_='mentor').span.string
                A['hours'] = s.find('div', class_='time time-first')
                if A['hours']:
                    A['hours'] = A['hours'].span.string
                    A['minutes'] = s.find_all(
                        'div',
                        class_='time')[1].span.string
                else:
                    del A['hours']

                for _ in A.keys():
                    # IRC and Unicode don't mix very well, it seems.
                    A[_] = str(A[_])

                self.msg(channel, A['title'])
                if 'hours' in A:
                    self.msg(channel, 'Status: ' + A['status'] +
                             ' ({hours} hours, {minutes} minutes left)'.format(
                        hours=A['hours'], minutes=A['minutes']))
                else:
                    self.msg(channel, 'Status: ' + A['status'])
                self.msg(channel, 'Mentor(s): ' + A['mentor'])

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
    f = BotFactory(sys.argv)
    reactor.connectTCP("irc.freenode.net", 6667, f)
    reactor.run()
