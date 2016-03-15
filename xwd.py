#!/usr/bin/env python3

from __future__ import print_function, unicode_literals

import struct
import sys

# :python3:buffer: we need to get a binary stream in both
# Python 2 and Python 3.
def binary(stream):
    if hasattr(stream, 'buffer'):
        return stream.buffer
    else:
        return stream

class FormatError(Exception):
    pass

class BigEndian:
    def __str__(self):
        return '>'

class LittleEndian:
    def __str__(self):
        return '<'

def xwd_open(f):
    header = f.read(8)
    size_be, = struct.unpack('>L', header[:4])
    size_le, = struct.unpack('<L', header[:4])
    # Exactly one of these should be "reasonable" (< 65536)
    if [size_be < 65536, size_le < 65536].count(True) != 1:
        raise FormatError(
          "Cannot determine endianness from header size: {!r}".format(
            header[:4]))

    if size_be < 65336:
        fmt = '>L'      # big endian
        size = size_be
    else:
        fmt = '>L'      # little endian
        size = size_le
    print(fmt)

    version, = struct.unpack(fmt, header[4:8])
    if version != 7:
        raise FormatError(
          "Sorry only version 7 supported, not version {!r}".format(
            version))

    fields = [
        'pixmap_format',
        'pixmap_depth',
        'pixmap_width',
        'pixmap_height',
        'xoffset',
        'byte_order',
        'bitmap_unit',
        'bitmap_bit_order',
        'bitmap_pad',
        'bits_per_pixel',
        'bytes_per_line',
        'visual_class',
        'red_mask',
        'green_mask',
        'blue_mask',
        'bits_per_rgb',
        'colormap_entries',
        'ncolors',
        'window_width',
        'window_height',
        'window_x',
        'window_y',
        'window_bdrwidth',
    ]

    res = dict(header_size=size, version=version)
    for field in fields:
        v, = struct.unpack(fmt, f.read(4))
        res[field] = v
        print(field, v)


def main():
    inp = binary(sys.stdin)
    xwd = xwd_open(inp)

if __name__ == '__main__':
    main()
