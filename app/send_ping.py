# -*- coding: utf-8 -*-

from discovery import EndPoint, PingNode, PingServer

my_endpoint = EndPoint(u'192.168.1.192', 30303, 30303)
their_endpoint = EndPoint(u'127.0.0.1', 30303, 30303)

server = PingServer(my_endpoint)

listen_thread = server.udp_listen()
listen_thread.start()

server.ping(their_endpoint)
