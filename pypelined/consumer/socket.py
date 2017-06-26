from __future__ import absolute_import
import socket

import chainlet


class BaseSocket(chainlet.ChainLink):
    def __init__(self, host, port, encoding='utf-8'):
        self._address = (host, port)
        self.encoding = encoding

    @property
    def host(self):
        """Host messages are sent to"""
        return self._address[0]

    def port(self):
        """Port messages are sent to"""
        return self._address[1]

    def _encode(self, message):
        if self.encoding:
            return message.encode(self.encoding)
        return message

    def __repr__(self):
        if self.encoding:
            return '%s(%s, %s, %s)' % (self.__class__.__name__, self.host, self.port, self.encoding)
        return '%s(%s, %s)' % (self.__class__.__name__, self.host, self.port)


class UDPSocket(BaseSocket):
    """
    Chainable socket that sends data chunks via UDP using IPv4

    :param host: host to send messages to as a name or IPv4 address
    :type host: str
    :param port: port to send messages to
    :type port: int
    """
    def __init__(self, host, port):
        super(UDPSocket, self).__init__(host, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def chainlet_send(self, value=None):
        """Send pipeline value to ``host:port`` without consuming it"""
        message = self._encode(value)
        while message:
            message = message[self._socket.sendto(message, self._address):]
        return value


class UDP6Socket(UDPSocket):
    """
    Chainable socket that sends data chunks via UDP using IPv6

    :param host: host to send messages to as a name or IPv6 address
    :type host: str
    :param port: port to send messages to
    :type port: int
    """
    def __init__(self, host, port):
        super(UDP6Socket, self).__init__(host, port)
        self._socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

udp_send = UDPSocket
udp6_send = UDP6Socket

__all__ = ['udp_send', 'udp6_send']
