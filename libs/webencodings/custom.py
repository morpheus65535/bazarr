"""

    webencodings.custom
    ~~~~~~~~~~~~~~~~~~~

    An implementation of custom "replacement" and "x-user-defined" encodings.

    :copyright: Copyright 2012 by Simon Sapin
    :license: BSD, see LICENSE for details.

"""

import codecs

# Abstract and common classes

class Codec(codecs.Codec):
    encoding_table = None
    decoding_table = None

    def encode(self, input, errors='strict'):
        return codecs.charmap_encode(input, errors, self.encoding_table)

    def decode(self, input, errors='strict'):
        return codecs.charmap_decode(input, errors, self.decoding_table)


class IncrementalEncoder(codecs.IncrementalEncoder):
    encoding_table = None

    def encode(self, input, final=False):
        return codecs.charmap_encode(input, self.errors, self.encoding_table)[0]


class IncrementalDecoder(codecs.IncrementalDecoder):
    decoding_table = None

    def decode(self, input, final=False):
        return codecs.charmap_decode(input, self.errors, self.decoding_table)[0]


class StreamWriter(Codec, codecs.StreamWriter):
    pass


class StreamReader(Codec, codecs.StreamReader):
    pass


# "x-user-defined" encoding

user_decoding_table = ''.join(chr(c if c < 128 else c + 0xF700) for c in range(256))
user_encoding_table = codecs.charmap_build(user_decoding_table)

class UserCodec(Codec):
    decoding_table = user_decoding_table
    encoding_table = user_encoding_table

class UserIncrementalEncoder(IncrementalEncoder):
    encoding_table = user_encoding_table

class UserIncrementalDecoder(IncrementalDecoder):
    decoding_table = user_decoding_table

user_codec_info = codecs.CodecInfo(
    name='x-user-defined',
    encode=UserCodec().encode,
    decode=UserCodec().decode,
    incrementalencoder=UserIncrementalEncoder,
    incrementaldecoder=UserIncrementalDecoder,
    streamreader=StreamReader,
    streamwriter=StreamWriter,
)


# "replacement" encoding

class ReplacementCodec(Codec):
    decoding_table = encoding_table = ''

class ReplacementIncrementalEncoder(IncrementalEncoder):
    encoding_table = ''

class ReplacementIncrementalDecoder(IncrementalDecoder):
    decoding_table = ''

replacement_codec_info = codecs.CodecInfo(
    name='replacement',
    encode=ReplacementCodec().encode,
    decode=ReplacementCodec().decode,
    incrementalencoder=ReplacementIncrementalEncoder,
    incrementaldecoder=ReplacementIncrementalDecoder,
    streamreader=StreamReader,
    streamwriter=StreamWriter,
)
