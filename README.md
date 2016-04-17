# xwd2png - X Window Dump to Portable Network Graphic

Select window and convert to PNG file:

```
xwd | ./xwd.py
```

# Notes for the curious

XWDFile.h comes from
http://www.opensource.apple.com/source/X11/X11-0.40.80/xc/include/XWDFile.h?txt

`xwud -dumpheader` can be a useful diagnostic.

Different windows may have dumps in different formats.
For example,
my `Terminal` dump has `pixmap depth` 32;
the `display.im6` (ImageMagick) has `pixmap depth` 24.
(or possibly this is me taking dumps on different laptops; i'm
not sure)

# Visual Class 5

Discovered that (on `bay` at any rate) trying to `xwd` an `xmag`
window creates a Visual Class 5 dump, which this module
currently fails to decode.

# 24- and 32-bit

On a modern (2016) Linux box it seems that everything is either
24- or 32-bit.

`file` reports PixmapDepth. Not sure what "24-bit" means.
Both the 24-bit sample xwd file I have and
the 32-bit file
have 32-bits per pixel
in XRGB8 format.

Reading a series of 32-bit ints then masking off the top 8 bits
could be quite slow in Python.
Might be better to treat a row as an array of octets,
then remove every 4th octet: del `a[0::4]`
