import logging as log

class StyleBase(object):

    color = None
    font_family = None
    background_color = None
    border_color = None
    font_style = None
    text_align = None
    _font_size_points = None # points

    @property
    def font_size(self):
        return self._font_size_points

    @font_size.setter
    def font_size(self, value):
        if 'pt' in value:
            value = int(value.replace('pt','')) 
        elif 'px' in value:
            log.warning("font-size does not (yet) support pixel sizes") # TODO: support pixel
            self._font_size_points = None
            return
        else:
            log.warning("assuming font-size is in points")

        self._font_size_points = int(value)

    def style_from_string(self, in_str):
        
        for attr in in_str.split(";"):
            if attr.strip() == '': continue
            k,v = attr.split(":")
            value = v.strip()
            key = k.strip().replace("-", "_")
            if not hasattr(self, key):
                log.warn("Unknown style attribute %s: %s" % (key,value))
                continue

            setattr(self, key, value)

