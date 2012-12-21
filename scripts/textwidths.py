#!/usr/bin/env python
r'''
Output is in format [fontname]{defualt_width:x, values: {character: (width, kern_pairs)}} and an example looks like this::


  {'Arial': {'default_width': 152,
           'values': {'\x00': (192,
                               {'A': -1,
                                '\\': -1,
                                '_': -3,
                                'j': -12,
                                '\xaf': -4,
                                '\xc0': -1,
                                '\xc1': -1,
                                '\xc2': -1,
                                '\xc3': -1,
                                '\xc4': -1,
                                '\xc5': -1,
                                '\xce': -4,
                                '\xee': -3}),
                      ....
                      'P': (171,
                            {' ': -5,
                             ',': -33,
                             '.': -33,
                             'A': -20,
                             '\\': -1,
                             '_': -3,
                             'j': -12,
                             '\xa0': -5,
                             '\xaf': -4,
                             '\xc0': -1,
                             '\xc1': -1,
                             '\xc2': -1,
                             '\xc3': -1,
                             '\xc4': -1,
                             '\xc5': -1,
                             '\xce': -4,
                             '\xee': -3}),

The scale of all numbers are 256 points. 

'''

import Image, ImageDraw, ImageFont


FONT_PATH = "/usr/share/fonts/truetype/msttcorefonts/"
FONT_EXT = ".ttf"

def get_width(font, char_str):
    im = Image.new('RGBA', (100, 100), (0, 0, 0, 0)) 
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT_PATH+font+FONT_EXT, 256)
    width, height = draw.textsize(char_str, font)
    del draw
    return width, char_str


font_list = [
    "Andale_Mono",
    "Arial_Black",
    "Arial_Bold_Italic",
    "Arial_Bold",
    "Arial_Italic",
    "Arial",
    "Comic_Sans_MS_Bold",
    "Comic_Sans_MS",
    "Courier_New",
    "Georgia_Bold",
    "Georgia_Italic",
    "Georgia",
    "Impact",
    "Times_New_Roman_Bold_Italic",
    "Times_New_Roman_Bold",
    "Times_New_Roman_Italic",
    "Times_New_Roman",
    "Trebuchet_MS_Bold_Italic",
    "Trebuchet_MS_Bold",
    "Trebuchet_MS_Italic",
    "Trebuchet_MS",
    "Verdana_Bold_Italic",
    "Verdana_Bold",
    "Verdana_Italic",
    "Verdana",
    "Webdings",
]

fonts = {}

for font  in font_list:
    
    values = {}
    fonts[font] = dict(values=values,default_width=128)
    all_width = 0
    width_count = 0

    for i in range(256):

        width, char = get_width(font, chr(i))
        values[char] = (width, {})
        if width != 0:
            all_width += width
            width_count += 1

    fonts[font]['default_width'] = int(all_width / width_count)
    

    for lchar,ltables in values.items():
        lwidth = ltables[0]
        kerntable = ltables[1]
        for rchar,rtables in values.items():
            rwidth = rtables[0]
            pairwidth, pair = get_width(font, lchar+rchar )
            kern = pairwidth - (lwidth + rwidth)
            if kern != 0:
                kerntable[rchar] = kern

# write in binary pickle mode
import cPickle as pickle
f = open("font_data.bin","wb")
pickle.dump(fonts,f,True)
f.close()



