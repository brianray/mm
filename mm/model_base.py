import logging

log = logging.getLogger(__name__)

class BaseFieldType(object):
    header_title = u''
    def __init__(self, data):
        self.data = data


class DateFieldType(BaseFieldType):
    pass

class TimeFieldType(BaseFieldType):
    pass

class DateTimeFieldType(BaseFieldType):
    pass

class IntFieldType(BaseFieldType):
    pass

class FloatFieldType(BaseFieldType):
    pass

class DecimalFieldType(BaseFieldType):
    pass

class StringFieldType(BaseFieldType):
    pass

class BoolFieldType(BaseFieldType):
    pass

class URLFieldType(BaseFieldType):
    pass

class ImageFieldType(BaseFieldType):
    pass

class NoneFieldType(BaseFieldType):
    pass



class DataModel(object):
    """ Data Model creates a list of system defined data types in self.field_headers"""

    def __init__(self, data, order=None):
        """ constructor takes data as a tuple or list"""
        self.field_headers = []
        if len(data) == 0:
            raise Exception("Can not make spreadsheets with an empty set")
        first_data = data[0]
        if type(first_data) == dict and len(first_data) > 0:
            keys = []
            if order:
                # add in this order it was explicitly set
                keys = order
            else:                
                # no order set, just sort
                keys= first_data.keys()
                keys.sort()
           
            for k in keys:
                # first we figure out the type
                # to use in the instance
                field_type_class = self.figure_out_type(data[0][k])
                field_type_class.header_title = k
                self.field_headers.append(field_type_class)
                log.info("created field type %s for %s" %(field_type_class,k))

    def figure_out_type(self,item):
        if type(item) == unicode or type(item) == str:
            return  StringFieldType
        
        return NoneFieldType






