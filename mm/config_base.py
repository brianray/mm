

class ConfigBase(object):
    """ Holds the configuration """
    
    def __init__(self, config=None):
        if config:
            for k,v in config.items():
                setattr(self, k, v)

    # default settings
    headers = True
    header_style = "color: #fffff; font-family: arial; background-color: #1122CC"
    freeze_col = 0
    freeze_row = 1
    row_styls = (
        "color: #000000; font-family: arial; background-color: #FDF6E5",
        "color: #999999;  font-family: arial; background-color: #000000"   # Alternate
    )
    adjust_all_col_width = True



