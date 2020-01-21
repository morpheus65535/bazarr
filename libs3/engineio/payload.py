import six

from . import packet

from six.moves import urllib


class Payload(object):
    """Engine.IO payload."""
    max_decode_packets = 16

    def __init__(self, packets=None, encoded_payload=None):
        self.packets = packets or []
        if encoded_payload is not None:
            self.decode(encoded_payload)

    def encode(self, b64=False, jsonp_index=None):
        """Encode the payload for transmission."""
        encoded_payload = b''
        for pkt in self.packets:
            encoded_packet = pkt.encode(b64=b64)
            packet_len = len(encoded_packet)
            if b64:
                encoded_payload += str(packet_len).encode('utf-8') + b':' + \
                    encoded_packet
            else:
                binary_len = b''
                while packet_len != 0:
                    binary_len = six.int2byte(packet_len % 10) + binary_len
                    packet_len = int(packet_len / 10)
                if not pkt.binary:
                    encoded_payload += b'\0'
                else:
                    encoded_payload += b'\1'
                encoded_payload += binary_len + b'\xff' + encoded_packet
        if jsonp_index is not None:
            encoded_payload = b'___eio[' + \
                              str(jsonp_index).encode() + \
                              b']("' + \
                              encoded_payload.replace(b'"', b'\\"') + \
                              b'");'
        return encoded_payload

    def decode(self, encoded_payload):
        """Decode a transmitted payload."""
        self.packets = []

        if len(encoded_payload) == 0:
            return

        # JSONP POST payload starts with 'd='
        if encoded_payload.startswith(b'd='):
            encoded_payload = urllib.parse.parse_qs(
                encoded_payload)[b'd'][0]

        i = 0
        if six.byte2int(encoded_payload[0:1]) <= 1:
            # binary encoding
            while i < len(encoded_payload):
                if len(self.packets) >= self.max_decode_packets:
                    raise ValueError('Too many packets in payload')
                packet_len = 0
                i += 1
                while six.byte2int(encoded_payload[i:i + 1]) != 255:
                    packet_len = packet_len * 10 + six.byte2int(
                        encoded_payload[i:i + 1])
                    i += 1
                self.packets.append(packet.Packet(
                    encoded_packet=encoded_payload[i + 1:i + 1 + packet_len]))
                i += packet_len + 1
        else:
            # assume text encoding
            encoded_payload = encoded_payload.decode('utf-8')
            while i < len(encoded_payload):
                if len(self.packets) >= self.max_decode_packets:
                    raise ValueError('Too many packets in payload')
                j = encoded_payload.find(':', i)
                packet_len = int(encoded_payload[i:j])
                pkt = encoded_payload[j + 1:j + 1 + packet_len]
                self.packets.append(packet.Packet(encoded_packet=pkt))
                i = j + 1 + packet_len
