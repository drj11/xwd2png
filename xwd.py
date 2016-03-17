#!/usr/bin/env python3

from __future__ import division, print_function, unicode_literals

import getopt
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

class NotImplemented(Exception):
    pass

class BigEndian:
    pass

class LittleEndian:
    pass

class XWD:
    def __init__(self, input, info=None):
        if info:
            self.__dict__.update(info)
        self.info_dict = info
        self.input = input

    def info(self):
        return dict(self.info_dict)

    def __iter__(self):
        while True:
            bs = self.input.read(self.bytes_per_line)
            if len(bs) == 0:
                break
            yield bs

    def pixels(self, row):
        bpp = self.bits_per_pixel // 8
        if bpp * 8 != self.bits_per_pixel:
            raise NotImplemented("Cannot handle bits_per_pixel of {!r}".format(
              self.bits_per_pixel))

        for s in range(0, len(row), bpp):
            pix = row[s:s+bpp]
            # pad to 4 bytes
            pad = b'\x00' * (4 - len(pix))
            if self.endian == BigEndian:
                fmt = ">L"
                pix = pad + pix
            else:
                fmt = "<L"
                pix = pix + pad
            v, = struct.unpack(fmt, pix)
            yield v

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
        endian = BigEndian
        fmt = '>L'
        size = size_be
    else:
        endian = LittleEndian
        fmt = '>L'
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

    res = dict(header_size=size, version=version, endian=endian)
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

    xwd = XWD(input=f, info=res)
    return xwd

def main(argv=None):
    if argv is None:
        argv = sys.argv

    opts, args = getopt.getopt(argv[1:], 'i', ['info'])

    os = [o for o,v in opts]

    if len(args) == 0:
        inp = binary(sys.stdin)
    else:
        inp = open(args[0], 'rb')

    xwd = xwd_open(inp)

    if '-i' in os or '--info' in os:
        info = xwd.info()
        for k,v in sorted(info.items()):
            if 'mask' in k:
                v = "{:#x}".format(v)
            print(k, v)
        return 0

    for row in xwd:
        for pixel in xwd.pixels(row):
            continue
            print("{:x}".format(pixel))
        print(row)

if __name__ == '__main__':
    main()
