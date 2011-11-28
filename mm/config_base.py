

class ConfigBase(object):
    """ Holds the configuration """
    
    def __init__(self, config=None):
        if config:
            for k,v in config.items():
                setattr(self, k, v)

    # default settings
    headers = True

 




