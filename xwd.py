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

class XWD:
    def __init__(self, **k):
        self.__dict__.update(k)

    def __iter__(self):
        while True:
            bs = self.input.read(self.bytes_per_line)
            if len(bs) == 0:
                break
            yield bs

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

    header_size = 8 + 4 * len(fields)
    window_name_len = size - header_size

    if window_name_len <= 0:
        raise FormatError(
          "Size in header, {!r}, is too small".format(size))

    window_name = f.read(window_name_len)[:-1]
    res['window_name'] = window_name

    # read, but ignore, the colours
    E = fmt[0]  # endianness
    color_fmt = fmt + (E + 'H')*3 + 'B' + 'B'
    for i in range(res['ncolors']):
        f.read(12)
    print(f.tell())

    dump = XWD(input=f, **res)
    for row in dump:
        print(row)

def main():
    inp = binary(sys.stdin)
    xwd = xwd_open(inp)

if __name__ == '__main__':
    main()
