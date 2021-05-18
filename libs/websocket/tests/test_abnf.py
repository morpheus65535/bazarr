# -*- coding: utf-8 -*-
#
"""
websocket - WebSocket client library for Python

Copyright (C) 2010 Hiroki Ohtani(liris)

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

"""

import os
import websocket as ws
from websocket._abnf import *
import sys
import unittest
sys.path[0:0] = [""]


class ABNFTest(unittest.TestCase):

    def testInit(self):
        a = ABNF(0,0,0,0, opcode=ABNF.OPCODE_PING)
        self.assertEqual(a.fin, 0)
        self.assertEqual(a.rsv1, 0)
        self.assertEqual(a.rsv2, 0)
        self.assertEqual(a.rsv3, 0)
        self.assertEqual(a.opcode, 9)
        self.assertEqual(a.data, '')
        a_bad = ABNF(0,1,0,0, opcode=77)
        self.assertEqual(a_bad.rsv1, 1)
        self.assertEqual(a_bad.opcode, 77)

    def testValidate(self):
        a_invalid_ping = ABNF(0,0,0,0, opcode=ABNF.OPCODE_PING)
        self.assertRaises(ws._exceptions.WebSocketProtocolException, a_invalid_ping.validate, skip_utf8_validation=False)
        a_bad_rsv_value = ABNF(0,1,0,0, opcode=ABNF.OPCODE_TEXT)
        self.assertRaises(ws._exceptions.WebSocketProtocolException, a_bad_rsv_value.validate, skip_utf8_validation=False)
        a_bad_opcode = ABNF(0,0,0,0, opcode=77)
        self.assertRaises(ws._exceptions.WebSocketProtocolException, a_bad_opcode.validate, skip_utf8_validation=False)
        a_bad_close_frame = ABNF(0,0,0,0, opcode=ABNF.OPCODE_CLOSE, data=b'\x01')
        self.assertRaises(ws._exceptions.WebSocketProtocolException, a_bad_close_frame.validate, skip_utf8_validation=False)
        a_bad_close_frame_2 = ABNF(0,0,0,0, opcode=ABNF.OPCODE_CLOSE, data=b'\x01\x8a\xaa\xff\xdd')
        self.assertRaises(ws._exceptions.WebSocketProtocolException, a_bad_close_frame_2.validate, skip_utf8_validation=False)
        a_bad_close_frame_3 = ABNF(0,0,0,0, opcode=ABNF.OPCODE_CLOSE, data=b'\x03\xe7')
        self.assertRaises(ws._exceptions.WebSocketProtocolException, a_bad_close_frame_3.validate, skip_utf8_validation=True)

    def testMask(self):
        abnf_none_data = ABNF(0,0,0,0, opcode=ABNF.OPCODE_PING, mask=1, data=None)
        bytes_val = bytes("aaaa", 'utf-8')
        self.assertEqual(abnf_none_data._get_masked(bytes_val), bytes_val)
        abnf_str_data = ABNF(0,0,0,0, opcode=ABNF.OPCODE_PING, mask=1, data="a")
        self.assertEqual(abnf_str_data._get_masked(bytes_val), b'aaaa\x00')

    def testFormat(self):
        abnf_bad_rsv_bits = ABNF(2,0,0,0, opcode=ABNF.OPCODE_TEXT)
        self.assertRaises(ValueError, abnf_bad_rsv_bits.format)
        abnf_bad_opcode = ABNF(0,0,0,0, opcode=5)
        self.assertRaises(ValueError, abnf_bad_opcode.format)
        abnf_length_10 = ABNF(0,0,0,0, opcode=ABNF.OPCODE_TEXT, data="abcdefghij")
        self.assertEqual(b'\x01', abnf_length_10.format()[0].to_bytes(1, 'big'))
        self.assertEqual(b'\x8a', abnf_length_10.format()[1].to_bytes(1, 'big'))
        self.assertEqual("fin=0 opcode=1 data=abcdefghij", abnf_length_10.__str__())
        abnf_length_20 = ABNF(0,0,0,0, opcode=ABNF.OPCODE_BINARY, data="abcdefghijabcdefghij")
        self.assertEqual(b'\x02', abnf_length_20.format()[0].to_bytes(1, 'big'))
        self.assertEqual(b'\x94', abnf_length_20.format()[1].to_bytes(1, 'big'))
        abnf_no_mask = ABNF(0,0,0,0, opcode=ABNF.OPCODE_TEXT, mask=0, data=b'\x01\x8a\xcc')
        self.assertEqual(b'\x01\x03\x01\x8a\xcc', abnf_no_mask.format())

    def testFrameBuffer(self):
        fb = frame_buffer(0, True)
        self.assertEqual(fb.recv, 0)
        self.assertEqual(fb.skip_utf8_validation, True)
        fb.clear
        self.assertEqual(fb.header, None)
        self.assertEqual(fb.length, None)
        self.assertEqual(fb.mask, None)
        self.assertEqual(fb.has_mask(), False)


if __name__ == "__main__":
    unittest.main()
