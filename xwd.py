#!/usr/bin/env python3

from __future__ import division, print_function, unicode_literals

import getopt
import itertools
import re
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
            yield list(itertools.chain(*self.pixels(bs)))

    def __len__(self):
        return self.pixmap_height

    def pixels(self, row):

        # Check visual_class.
        # The following table from http://www.opensource.apple.com/source/tcl/tcl-87/tk/tk/xlib/X11/X.h is assumed:
        # StaticGray    0
        # GrayScale     1
        # StaticColor   2
        # PseudoColor   3
        # TrueColor     4
        # DirectColor   5

        if self.visual_class != 4:
            # TrueColor
            raise NotImplemented("Cannot handle visual_class {!r}".format(self.visual_class))

        # bytes per pixel
        bpp = self.bits_per_pixel // 8
        if bpp * 8 != self.bits_per_pixel or bpp > 4:
            raise NotImplemented("Cannot handle bits_per_pixel of {!r}".format(
              self.bits_per_pixel))

        red_shift = ffs(self.red_mask)
        green_shift = ffs(self.green_mask)
        blue_shift = ffs(self.blue_mask)

        for s in range(0, len(row), bpp):
            pix = row[s:s+bpp]
            # pad to 4 bytes
            pad = b'\x00' * (4 - len(pix))
            if self.byte_order == 1:
                fmt = ">L"
                pix = pad + pix
            else:
                fmt = "<L"
                pix = pix + pad
            v, = struct.unpack(fmt, pix)
            r = (v & self.red_mask) >> red_shift
            g = (v & self.green_mask) >> green_shift
            b = (v & self.blue_mask) >> blue_shift
            yield (r,g,b)


def xwd_open(f):
    # From XWDFile.h:
    # "Values in the file are most significant byte first."
    fmt = '>L'

    header = f.read(8)

    header_size, = struct.unpack(fmt, header[:4])

    # There are no magic numbers, so as a sanity check,
    # we check that the size is "reasonable" (< 65536)
    if header_size >= 65536:
        raise FormatError(
          "header_size too big: {!r}".format(header[:4]))

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

    res = dict(header_size=header_size, version=version)
    for field in fields:
        v, = struct.unpack(fmt, f.read(4))
        res[field] = v

    xwd_header_size = 8 + 4 * len(fields)
    window_name_len = header_size - xwd_header_size

    if window_name_len <= 0:
        raise FormatError(
          "Size in header, {!r}, is too small".format(size))

    window_name = f.read(window_name_len)[:-1]
    res['window_name'] = window_name

    # read, but ignore, the colours
    color_fmt = fmt + '>H'*3 + 'B' + 'B'
    for i in range(res['ncolors']):
        f.read(12)

    xwd = XWD(input=f, info=res)
    return xwd

def ffs(x):
    """
    Returns the index, counting from 0, of the
    least significant set bit in `x`.
    """
    return (x&-x).bit_length()-1

def main(argv=None):
    if argv is None:
        argv = sys.argv

    opts, args = getopt.getopt(argv[1:], 'i', ['info', 'raw'])

    options = [o for o,v in opts]

    if len(args) == 0:
        inp = binary(sys.stdin)
    else:
        inp = open(args[0], 'rb')

    xwd = xwd_open(inp)

    if '-i' in options or '--info' in options:
        info = xwd.info()
        for k,v in sorted(info.items()):
            if 'mask' in k:
                v = "{:#x}".format(v)
            print(k, v)
        return 0

    if '--raw' in options:
        for row in xwd:
            print(*row)
        return 0

    try:
        inp.name
    except AttributeError:
        output_name = "out.png"
    else:
        output_name = re.sub(r'(\..*|)$', '.png', inp.name)
        if output_name == inp.name:
            # avoid overwriting input,
            # if, for some reason,
            # input is mysteriously named: input.png
            output_name += '.png'

    import png
    apng = png.from_array(xwd, "RGB;8")
    apng.save(output_name)

if __name__ == '__main__':
    main()
