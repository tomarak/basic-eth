import socket
import threading
import time
import struct
import rlp
from crypto import keccak256
from secp256k1 import PrivateKey
from ipaddress import ip_address


class EndPoint(object):
    """Ping communication end point class."""

    def __init__(self, address, udp_port, tcp_port):
        """Initialize end point class."""
        # The address is passed to the ip_address package in order
        # to later convert the address from dot format to binary format
        self.address = ip_address(address)
        self.udp_port = udp_port
        self.tcp_port = tcp_port

    def pack(self):
        """
        Prepare the object for encoding.

        - The IP address is converted to a BE encoded 4-byte address
        - RLP specification says "Ethereum integers must be represented in big
        endian binary form with no leading zeroes"
        - Port data types are also unsigned 16-bit integers
        """
        return [
            self.address.packed,
            struct.pack(">H", self.udp_port),
            struct.pack(">H", self.tcp_port),
        ]


class PingNode(object):
    """Ping node class."""

    PACKET_TYPE = '\x01';
    VERSION = '\x03';

    def __init__(self, endpoint_from, endpoint_to):
        """Initialize ping node class."""
        self.endpoint_from = endpoint_from
        self.endpoint_to = endpoint_to

    def pack(self):
        """Prepare the object for encoding."""
        return [
            self.VERSION,
            self.endpoint_from.pack(),
            self.endpoint_to.pack,
            struct.pack(">I", time.time() + 60),
        ]


class PingServer(object):
    def __init__(self, my_endpoint):
        self.endpoint = my_endpoint

        private_key_file = open('priv_key', 'r')
        private_key_serialized = private_key_file.read()
        private_key_file.close()

        self.private_key = PrivateKey()
        self.private_key.deserialize(private_key_serialized)

    def wrap_packet(self, packet):
        payload = packet.packet_type + rlp.encode(packet.pack())
        sig = self.priv_key.ecdsa_sign_recoverable(keccak256(payload), raw=True)
        sig_serialize = self.private_key.ecdsa_recoverable_serialize(sig)
        payload = sig_serialized[0] + chr(sig_serailized[1] + payload)

        payload_hash = keccak256(payload)
        return payload_hash + payload

    def udp_listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', self.endpoint.udp_port))

        def receive_ping():
            print 'listening...'
            data, addr = sock.recvfrom(1024)
            print 'received message[{}]'.format(addr)

        return threading.Thread(target=receive_ping)

    def ping(self, endpoint):
        sock = socket.socket(socket.AF_INET), socket.SOCK_DGRAM
        ping = PingNode(self.endpoint, endpoint)
        message = self.wrap_packet(ping)
        print "sending ping."
        sock.sendto(
            message,
            (endpoint.address.exploded, endpoint.udp_port)
        )
