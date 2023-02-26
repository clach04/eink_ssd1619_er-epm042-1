from __future__ import print_function

import logging
import os
import sys

try:
    from PIL import Image
except ImportError:
    try:
        import Image    # http://www.pythonware.com/products/pil/
    except ImportError:
        Image = None


import epd


log_format = '%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s'
logging.basicConfig(format=log_format)
log = logging.getLogger('asusdisplay')
log.setLevel(logging.NOTSET)  # only logs; WARNING, ERROR, CRITICAL
log.setLevel(logging.DEBUG)

MAX_IMAGE_SIZE = (epd.EPD_WIDTH, epd.EPD_HEIGHT)


def simpleimage_resize(im):
    log.debug('im.size %r', im.size)
    if im.size[1] > im.size[0]:
        log.debug('rotate')
        #im = im.rotate(90)
        #im = im.transpose(Image.ROTATE_90)
        im = im.transpose(Image.ROTATE_270)  # TODO be more efficient to rotate after reducing size
    log.debug('im.size %r', im.size)
    if im.size > MAX_IMAGE_SIZE:
        log.debug('resizing')
        """resize - maintain aspect ratio
        NOTE PIL thumbnail method does not increase
        if new size is larger than original
        2 passes gives good speed and quality
        """
        im.thumbnail((MAX_IMAGE_SIZE[0] * 2, MAX_IMAGE_SIZE[1] * 2))
        im.thumbnail(MAX_IMAGE_SIZE, Image.ANTIALIAS)

    # image is not too big, but it may be too small
    # _may_ need to add white (black) bar(s)
    if im.size < MAX_IMAGE_SIZE:
        log.debug('too small - add bar')
        im = im.convert('RGB')  # convert to RGB
        #bg_col = (0, 0, 0)
        #bg_col = (0x00, 0x00, 0x00)
        bg_col = (0xff, 0xff, 0xff)
        background = Image.new('RGB', MAX_IMAGE_SIZE, bg_col)
        x, y = im.size
        #background.paste(im, (0, 0, x, y))  # does not center/centre
        x1 = int(.5 * background.size[0]) - int(.5 * im.size[0])
        y1 = int(.5 * background.size[1]) - int(.5 * im.size[1]) -1
        x2 = int(.5 * background.size[0]) + int(.5 * im.size[0])
        y2 = int(.5 * background.size[1]) + int(.5 * im.size[1])
        log.debug('im.size %r', background.size)
        log.debug('offsets %r', ((x1, y1, x2, y2),))
        background.paste(im, (x1, y1, x2, y2))  # center/centre
        im = background
    
    return im


print('Python %s on %s' % (sys.version, sys.platform))

filename = sys.argv[1]

color_image = Image.open(filename)
print(type(color_image))
print(color_image)
color_image = simpleimage_resize(color_image)
color_image = color_image.convert('RGB')

palette_three_colors = [
    0x00, 0x00, 0x00,  # white
    0xff, 0xff, 0xff,  # black
    0xff, 0x00, 0x00,  # red
]
palette_three_colors = palette_three_colors + ([0x00] * (3 * 256 - len(palette_three_colors)))

image_palette = Image.new("P", (1, 1), 0)
image_palette.putpalette(palette_three_colors)

im_three_colors = color_image.quantize(palette=image_palette)
#im_three_colors.show()


palette_black_colors = [
    0x00, 0x00, 0x00,  # white
    0xff, 0xff, 0xff,  # black
    0x00, 0x00, 0x00,  # red - wiped out
]
palette_black_colors = palette_black_colors + ([0x00] * (3 * 256 - len(palette_black_colors)))
palette_red_colors = [
    0xff, 0xff, 0xff,  # white
    0xff, 0xff, 0xff,  # black - wiped out
    0x00, 0x00, 0x00,  # red
]  # NOTE TODO FIXME inverted.... DISPLAY_UPDATE_CONTROL_1...(0x80) # Inverse RED RAM content
palette_red_colors = palette_red_colors + ([0x00] * (3 * 256 - len(palette_red_colors)))

im_three_colors.putpalette(palette_black_colors)
black_image = im_three_colors.convert('1')  # 1bpp
#black_image.show()

im_three_colors.putpalette(palette_red_colors)
red_image = im_three_colors.convert('1')  # 1bpp
#red_image.show()

display = epd.Epd()

try:
    display.clear()

    if Image:
        display.display(black_image.tobytes(), red_image.tobytes())
        log.info('image now displaying, sleeping for 30 secs')
        epd.delay_ms(30 * 1000)
finally:
    display.sleep()
    display.close()
