import logging
log = logging.getLogger(__name__)


class DjangoGrid(object):

    def populate(self, indata):
        for required in ('row_count', 'col_count', 'headers'):
            if not hasattr(self, required):
                raise Exception("missing required attribute to Grid: %s" % required)
        # create a grid
        self.grid_data = [[None] * self.col_count for i in range(self.row_count)]

        # now populate
        # this is pass one
        # want to do as much processing here as we can
        # we populate left to right, top to bottom
        for row_id in range(self.row_count):
            row = indata[row_id]
            for col_id in range(self.col_count):
                field_type_class = self.headers[col_id]
                data = getattr(row, self.titles[col_id])
                self.grid_data[row_id][col_id] = field_type_class(data)

                #Ilport pdb; pdb.set_trace()
        log.info("populated grid %sX%s" % (self.row_count, self.col_count))
