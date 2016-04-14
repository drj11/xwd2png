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

`file` reports PixmapDepth. Not sure what "24-bit" means. The
24-bit sample xwd file I have has 32-bits per pixel in RGB8
format.
