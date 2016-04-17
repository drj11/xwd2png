#!/usr/bin/env python3

from __future__ import division, print_function, unicode_literals

import getopt
import itertools
import json
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


class Channel:
    def __init__(self, **k):
        self.__dict__.update(k)

class XWD:
    def __init__(self, input, xwd_header=None):
        if xwd_header:
            self.__dict__.update(xwd_header)
        self.xwd_header = xwd_header
        self.info_dict = dict(
          h=self.pixmap_height,
          w=self.pixmap_width,
          xwd_header=xwd_header,
          )
        self.input = input

    def info(self):
        return dict(self.info_dict)

    def uni_format(self):
        """
        Return the "universal format" for the XWD file.
        As a side effect, compute and cache various
        intermediate values (such as shifts and depths).
        """

        if '_uni_format' in self.__dict__:
            return self._uni_format

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

        # Associate each mask with its channel colour.
        channels = [
          Channel(name='R', mask=self.red_mask),
          Channel(name='G', mask=self.green_mask),
          Channel(name='B', mask=self.blue_mask),
          ]

        # If fails: some masks are the same.
        assert len(set(c.mask for c in channels)) == 3

        # Sort Most Significant first
        channels = sorted(channels, key=lambda x: x.mask, reverse=True)

        # Check that each mask is contiguous.
        for channel in channels:
            assert is_contiguous(channel.mask)

        # Check that each mask abuts the next...
        for channel, successor in zip(channels, channels[1:]):
            assert is_contiguous(channel.mask + successor.mask)

        # ... check that the last mask is on the right.
        # If fails: least significant bit is unused.
        # :todo: if it ever occurs in wild, implement a padding
        # channel, eg: RGB5X1.
        assert channels[-1].mask & 1

        # Annotate each channel with its shift and bitdepth.
        for c in channels:
            c.shift = ffs(c.mask)
            c.bits = (c.mask >> c.shift).bit_length()

        self.channels = channels

        v = ""
        for (bits, chans) in itertools.groupby(
          channels, lambda c: c.bits):
            v += ''.join(c.name for c in chans)
            v += str(bits)
        self._uni_format = v
        return self.uni_format()

    def __iter__(self):
        while True:
            bs = self.input.read(self.bytes_per_line)
            if len(bs) == 0:
                break
            yield list(itertools.chain(*self.pixels(bs)))

    def __len__(self):
        return self.pixmap_height

    def pixels(self, row):
        self.uni_format()

        # bytes per pixel
        bpp = self.bits_per_pixel // 8
        if bpp * 8 != self.bits_per_pixel or bpp > 4:
            raise NotImplemented("Cannot handle bits_per_pixel of {!r}".format(
              self.bits_per_pixel))

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

            cs = self.channels
            # Note: Could permute channels here
            # by permuting the `cs` list;
            # for example to convert BGR to RGB.
            pixel = tuple((v & c.mask) >> c.shift for c in cs)

            yield pixel


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

    xwd = XWD(input=f, xwd_header=res)
    return xwd

def ffs(x):
    """
    Returns the index, counting from 0, of the
    least significant set bit in `x`.
    """
    return (x&-x).bit_length()-1

def is_contiguous(x):
    """
    Check that x is a contiguous series of binary bits.
    """
    return is_power_of_2((x >> ffs(x)) + 1)

def is_power_of_2(x):
    assert x > 0
    return not(x & (x-1))

def main(argv=None):
    if argv is None:
        argv = sys.argv

    opts, args = getopt.getopt(argv[1:], 'i', ['info', 'raw'])

    options = [o for o,v in opts]

    if len(args) == 0:
        inp = binary(sys.stdin)
        out = binary(sys.stdout)
    else:
        inp = open(args[0], 'rb')
        out = None

    xwd = xwd_open(inp)

    if '-i' in options or '--info' in options:
        info = xwd.info()
        dprint(info)
        return 0

    if '--raw' in options:
        for row in xwd:
            print(*row)
        return 0

    if out is None:
        try:
            inp.name
        except AttributeError:
            out = "xwd2png_out.png"
        else:
            out = re.sub(r'(\..*|)$', '.png', inp.name)
            if out == inp.name:
                # avoid overwriting input,
                # if, for some reason,
                # input is mysteriously named: input.png
                output_name += '.png'

    format = xwd.uni_format()

    assert format == "RGB8"

    import png
    apng = png.from_array(xwd, "RGB;8")
    apng.save(out)

def dprint(o, indent=0):
    for k,v in sorted(o.items()):
        print(" "*indent, end="")
        if isinstance(v, dict):
            print(k+":")
            dprint(v, indent=indent+2)
            continue
        if 'mask' in k:
            v = "{:#x}".format(v)
        print(k, v)

if __name__ == '__main__':
    main()
