import os.path as path
from decorators import memoized
try:
    import cPickle as pickle
except:
    import pickle

LATEST_FONT_DATA = "font_data_ms_fonts.bin"

@memoized
def get_font_data():
    this_file_path = path.abspath(__file__)
    data_path = path.join( path.dirname(this_file_path), LATEST_FONT_DATA)
    pkl_file = open(data_path, 'rb')
    FONT_DATA = pickle.load(pkl_file)
    pkl_file.close()
    return FONT_DATA


@memoized
def get_character_data(font_name, char):
    font_data = get_font_data()
    font_name = font_name.replace("-","_").replace(" ","_")
    if font_name not in font_data:
        font_name = font_name.capitalize()
        if font_name not in font_data:
            raise Exception("no font data for font %s" % font_name)
    font_set = font_data[font_name]
    if char not in font_set['values']:
        return font_set['default_width'], {} # empty kerns
    return font_set['values'][char]

@memoized
def get_character_width(font_name, char):
    width, kerns = get_character_data(font_name, char)
    return width

@memoized
def get_kern_offset(font_name, char1, char2):
    width, kerns = get_character_data(font_name, char1)
    if char2 in kerns:
        return kerns[char2]
    return 0

@memoized
def get_string_width(font_name, point_size, char_string):
    out_width_256 = 0
    current_pos = 0
    str_length = len(char_string)
    for char in char_string:
        out_width_256 += get_character_width(font_name, char)
        if current_pos != (str_length-1):
            out_width_256 += get_kern_offset(font_name, char, char_string[current_pos+1])
        current_pos += 1
    return out_width_256 * ( point_size / 256.0 )

if __name__ == "__main__":
    get_character_data('Arial', 'A')
