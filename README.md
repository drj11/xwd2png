# xwd2png - X Window Dump to Portable Network Graphic

XWDFile.h comes from
http://www.opensource.apple.com/source/X11/X11-0.40.80/xc/include/XWDFile.h?txt

# Notes for the curious

`xwud -dumpheader` can be a useful diagnostic.

Different windows may have dumps in different formats.
For example,
my `Terminal` dump has `pixmap depth` 32;
the `display.im6` (ImageMagick) has `pixmap depth` 24.
