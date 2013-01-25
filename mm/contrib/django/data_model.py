import logging
from mm import model_base
import django.db.models.fields as fields

log = logging.getLogger(__name__)


class DjangoDataModel(object):
    """ Data Model creates a list of system defined data types in self.field_headers"""

    def __init__(self, data, order=None):
        """ constructor takes data as a tuple or list"""

        self.field_headers = []
        self.field_titles = []
        if data.count() == 0:
            raise Exception("Can not make spreadsheets with an empty set")
        first_data = data[0]

        header_types = {}
        for f in first_data._meta.fields:  # TODO: + obj._meta.many_to_many
            header_types[f.name] = self.figure_out_type(f)

        #TODO: 'if order' sort the list

        # assign data
        for verbose_name, field_type_class in header_types.items():

            # we add it to the 'class' so to be
            # used in every instance
            self.field_titles.append(verbose_name)
            self.field_headers.append(field_type_class)
            log.info("created field type %s for %s" % (field_type_class, verbose_name))

    def __serialize(obj):
        obj._meta.fields

    def _string_types(self):
        return [
            fields.CharField,
            fields.CommaSeparatedIntegerField,
            fields.IPAddressField,
            fields.SlugField,
            fields.TextField,
        ]

    def _int_types(self):
        return [
            fields.AutoField,
            fields.IntegerField,
            fields.PositiveIntegerField,
            fields.PositiveSmallIntegerField,
            fields.SmallIntegerField,

        ]

    def _bool_types(self):
        return [
            fields.BooleanField,
            fields.NullBooleanField,
        ]

    def _date_types(self):
        return [
            fields.DateField,
        ]

    def _time_types(self):
        return [
            fields.TimeField
        ]

    def _datetime_types(self):
        return [
            fields.DateTimeField,
        ]

    def _decimal_types(self):
        return [
            fields.DecimalField,
        ]

    def _float_types(self):
        return [
            fields.FloatField,
        ]

    def _none_types(self):
        return [
            fields.NullBooleanField
        ]

    def _url_types(self):
        return [
            fields.URLField
        ]

    def type_mapping(self):
        return (
            (self._string_types, model_base.StringFieldType),
            (self._int_types, model_base.IntFieldType),
            (self._bool_types, model_base.BoolFieldType),
            (self._date_types, model_base.DateFieldType),
            (self._time_types, model_base.TimeFieldType),
            (self._datetime_types, model_base.DateTimeFieldType),
            (self._decimal_types, model_base.DecimalFieldType),
            (self._float_types, model_base.FloatFieldType),
            (self._none_types, model_base.NoneFieldType),
            (self._url_types, model_base.URLFieldType),
        )

    def figure_out_type(self, item):
        """

This is how django stores types in sqlite3:

"AutoField" integer NOT NULL PRIMARY KEY,
"BooleanField" bool NOT NULL,
"CharField" varchar(50) NOT NULL,
"CommaSeparatedIntegerField" varchar(25) NOT NULL,
"DateField" date NOT NULL,
"DateTimeField" datetime NOT NULL,
"DecimalField" decimal NOT NULL,
"EmailField" varchar(75) NOT NULL,
"FloatField" real NOT NULL,
"IntegerField" integer NOT NULL,
"IPAddressField" char(15) NOT NULL,
"NullBooleanField" bool,
"PositiveIntegerField" integer unsigned NOT NULL,
"PositiveSmallIntegerField" smallint unsigned NOT NULL,
"SlugField" varchar(30) NOT NULL,
"SmallIntegerField" smallint NOT NULL,
"TextField" text NOT NULL,
"TimeField" time NOT NULL,
"URLField" varchar(100) NOT NULL
        """
        item_type = type(item)
        for func, mm_type in self.type_mapping():
            if item_type in func():
                return mm_type

        log.warn("Returning None type for type %s" % item_type)
        return model_base.NoneFieldType
