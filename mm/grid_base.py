import logging
from model_base import is_custom_mm_type

log = logging.getLogger(__name__)


class GridBase(object):

    def populate(self, indata):
        for required in ('row_count', 'col_count', 'headers', 'titles'):
            if not hasattr(self, required):
                raise Exception("missing required attribute to Grid: %s" % required)
        # create a grid
        self.grid_data = [[None] * self.col_count for i in range(self.row_count)]

        # now populate
        # this is pass one
        # want to do as much processing here as we can
        # we populate left to right, top to bottom
        for row_id in range(self.row_count):
            for col_id in range(self.col_count):
                field_type_class = self.headers[col_id]

                # headers from seelf.data_model.field_headers, sorted
                data = indata[row_id][self.titles[col_id]]  # direct data access
                if is_custom_mm_type(data):
                    # explicit type
                    self.grid_data[row_id][col_id] = data
                else:
                    # wrap in type from headers
                    self.grid_data[row_id][col_id] = field_type_class(data)

        log.info("populated grid %sX%s" % (self.row_count, self.col_count))
