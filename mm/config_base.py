

class ConfigBase(object):
    """ Holds the configuration """

    def get(self,key,default=None):
        if hasattr(self,key):
            return getattr(self,key)
        return default
    
    def __init__(self, config_dict=None):
        if config_dict:
            self.set_dict(config_dict)

    def set_dict(self, config_dict):
        for k,v in config_dict.items():
            setattr(self, k, v)


    # default settings
    headers = True
    header_style = "color: #ffffff; font-family: arial; background-color: #0000B3; font-size: 12pt; text-align: center"
    freeze_col = 0
    freeze_row = 1
    row_styles = (
        "color: #000000; font-family: arial; background-color: #666666; border-color: #ff0000",
        "color: #000000; font-family: arial; background-color: #FFFFFF"   # Alternate
    )
    adjust_all_col_width = True
    datetime_format = 'M/D/YY h:mm:ss'
    date_format = 'M/D/YY'
    time_format = "h:mm:ss"



