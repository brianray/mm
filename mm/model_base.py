import logging
from datetime import datetime
import inspect
import sys
from lib.font_data.decorators import memoized

log = logging.getLogger(__name__)

class BaseFieldType(object):
    header_title = u''
    def __init__(self, data):
        self.data = data
   
    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return u"%s (%s)" % ( self.header_title, type(self) )

class HeaderFieldType(BaseFieldType):
    pass

class DateFieldType(BaseFieldType):
    def __init__(self, data, format=None):
        self.format = format
        super(DateFieldType, self).__init__(data)

class TimeFieldType(BaseFieldType):
    pass

class DateTimeFieldType(BaseFieldType):

    def __init__(self, data):
        if data.tzinfo:
            data = data.replace(tzinfo=None) #excel can't handle
        super(DateTimeFieldType, self).__init__(data)


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
    def __init__(self, path, displayname=None):
        if not displayname:
            displayname = path
        self.displayname = displayname
        super(URLFieldType, self).__init__(path)


class ImageFieldType(BaseFieldType):
    def __init__(self, path, width=None, height=None):
        self.width = width
        self.height = height
        super(ImageFieldType, self).__init__(path)

class NoneFieldType(BaseFieldType):
    pass


@memoized
def get_members_list():
    return [ x[1] for x 
             in inspect.getmembers(sys.modules[__name__], inspect.isclass) 
             if issubclass(x[1], BaseFieldType)]


def is_custom_mm_type(inst):
    members = get_members_list()
    if type(inst) in members:
        return True
    return False

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
                # no order set, just get
                keys= first_data.keys()
           
            for k in keys:
                log.info("looking at %s ..." % data[0][k])
                if is_custom_mm_type(data[0][k]):
                    field_type_class = type(data[0][k])
                else:
                    # we figure out the type
                    field_type_class = self.figure_out_type(data[0][k])

                # we add it to the 'class' so to be
                # used in every instance
                field_type_class.header_title = k
                self.field_headers.append(field_type_class)
                log.info("created field type %s for %s" %(field_type_class,k))

    def figure_out_type(self,item):
        item_type= type(item)
        if item_type == unicode or item_type == str:
            return  StringFieldType

        elif item_type == int:
            return IntFieldType
                    
        elif item_type == datetime:
            return DateTimeFieldType

        log.warn("Returning None type for type %s" % item_type)
        return NoneFieldType






