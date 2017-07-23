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
    """Open sockets, sign and hash messages, send messages to other servers."""

    def __init__(self, my_endpoint):
        """
        Set up ping server.

        - Take an endpoint object (i.e: itself in the network space)
            - Used as a "from address" when sending packets
        - Load private key for server
        """
        self.endpoint = my_endpoint

        # Load and serialize private key
        private_key_file = open('private_key', 'r')
        private_key_serialized = private_key_file.read()
        private_key_file.close()

        # Ethereum uses secp256k1, an elliptic curve, for assymetric encryption
        self.private_key = PrivateKey()
        self.private_key.deserialize(private_key_serialized)

    def wrap_packet(self, packet):
        """
        Encode the packet.

        hash || signature || packet-type || packet-data
        """
        # Append the packet type to the RLP encoding of the packet data
        payload = packet.packet_type + rlp.encode(packet.pack())
        # Sign the hashed payload, use raw=True, cause we've already hashed,
        # and otherwise, the function would use its own hash function
        signature = self.private_key.ecdsa_sign_recoverable(
            keccak256(payload),
            raw=True,
        )
        # Creates a tuple
        signature_serialized = self.private_key.ecdsa_recoverable_serialize(signature)
        payload = signature_serialized[0] + chr(signature_serialized[1] + payload)

        payload_hash = keccak256(payload)
        return payload_hash + payload

    def udp_listen(self):
        """Listen for incoming transmissions"""
        # Create socket and bind it to the server's endpoint
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', self.endpoint.udp_port))

        def receive_ping():
            """Listen at the socket for incoming data"""
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
