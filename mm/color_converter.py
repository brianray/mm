from lib.font_data.decorators import memoized

excel_color_dict = {}

excel_color_dict['0, 0, 0'] = 0x08
excel_color_dict['255, 255, 255'] = 0x09
excel_color_dict['255, 0, 0'] = 0x0A
excel_color_dict['0, 255, 0'] = 0x0B
excel_color_dict['0, 0, 255'] = 0x0C
excel_color_dict['255, 255, 0'] = 0x0D
excel_color_dict['255, 0, 255'] = 0x0E
excel_color_dict['0, 255, 255'] = 0x0F
excel_color_dict['128, 0, 0'] = 0x10
excel_color_dict['0, 128, 0'] = 0x11
excel_color_dict['0, 0, 128'] = 0x12
excel_color_dict['128, 128, 0'] = 0x13
excel_color_dict['128, 0, 128'] = 0x14
excel_color_dict['0, 128, 128'] = 0x15
excel_color_dict['192, 192, 192'] = 0x16
excel_color_dict['128, 128, 128'] = 0x17
excel_color_dict['153, 153, 255'] = 0x18
excel_color_dict['153, 51, 102'] = 0x1A
excel_color_dict['255, 255, 204'] = 0x1C
excel_color_dict['204, 255, 255'] = 0x1D
excel_color_dict['102, 0, 102'] = 0x1E
excel_color_dict['255, 128, 128'] = 0x1F
excel_color_dict['0, 102, 204'] = 0x28
excel_color_dict['204, 204, 255'] = 0x29
excel_color_dict['0, 204, 255'] = 0x2A
excel_color_dict['204, 255, 204'] = 0x2B
excel_color_dict['255, 255, 153'] = 0x2C
excel_color_dict['153, 204, 255'] = 0x2D
excel_color_dict['255, 153, 204'] = 0x2E
excel_color_dict['204, 153, 255'] = 0x2F
excel_color_dict['255, 204, 153'] = 0x30
excel_color_dict['51, 102, 255'] = 0x31
excel_color_dict['51, 204, 204'] = 0x32
excel_color_dict['153, 204, 0'] = 0x33
excel_color_dict['255, 204, 0'] = 0x34
excel_color_dict['255, 153, 0'] = 0x35
excel_color_dict['255, 102, 0'] = 0x36
excel_color_dict['102, 102, 153'] = 0x37
excel_color_dict['150, 150, 150'] = 0x38
excel_color_dict['0, 51, 102'] = 0x39
excel_color_dict['51, 153, 102'] = 0x3A
excel_color_dict['0, 51, 0'] = 0x3B
excel_color_dict['51, 51, 0'] = 0x3C
excel_color_dict['153, 51, 0'] = 0x3D
excel_color_dict['51, 51, 153'] = 0x3E
excel_color_dict['51, 51, 51'] = 0x3F
  

@memoized
def rgb(c):
    split = (c[0:2], c[2:4], c[4:6])
    out = []
    for x in split:
        out.append(int(x,16)) 
    return out
  
@memoized  
def get_closest_rgb_match(hex):
    hex = hex.replace("#",'').strip()
    color_dict = excel_color_dict
    orig_rgb = rgb(hex)
    new_color = ''
    min_distance = 195075
    orig_r = orig_rgb[0]
    orig_g = orig_rgb[1]
    orig_b = orig_rgb[2]
    for key in color_dict.iterkeys():
        new_r = int(key.split(',')[0])
        new_g = int(key.split(',')[1])
        new_b = int(key.split(',')[2])
        r_distance = orig_r - new_r
        g_distance = orig_g - new_g
        b_distance = orig_b - new_b
        current_distance = (r_distance * r_distance) + (g_distance * g_distance) + (b_distance * b_distance)
        if current_distance < min_distance:
            min_distance = current_distance
            new_color = key
    return color_dict.get(new_color)
      

