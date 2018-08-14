import logging
from .model_base import is_custom_mm_type
log = logging.getLogger(__name__)


class GridBase(object):

    def populate(self, indata, config):
        for required in ('row_count', 'col_count', 'headers', 'titles'):
            if not hasattr(self, required):
                raise Exception("missing required attribute to Grid: %s" %
                                required)
        # create a grid
        self.grid_data = [[None] * self.col_count for i in range(self.row_count)]

        using_lists = False  # support for lists #2
        if type(indata[0]) != dict:
            using_lists = True

        # now populate
        # this is pass one
        # want to do as much processing here as we can
        # we populate left to right, top to bottom
        n_missing = 0
        for row_id in range(self.row_count):
            for col_id in range(self.col_count):
                field_type_class = self.headers[col_id]

                # headers from seelf.data_model.field_headers, sorted
                if using_lists:
                    try:
                        # direct data access lists
                        data = indata[row_id][col_id]
                    except IndexError:
                        log.warning('No index found in row %d column %d' %
                                    (row_id, col_id))
                        if config.INGORE_DATA_MISMATCH:
                            data = ''
                        n_missing += 1

                else:
                    if len(indata[row_id]) > self.col_count:
                        raise Exception("Data mismatch: Row %d has %d more columns than row 1" %
                                        ((row_id + 1), len(indata[row_id])-self.col_count))
                    try:
                        #direct data access dicts
                        data = indata[row_id][self.titles[col_id]]
                    except IndexError:
                        log.warning('No index found in row %d column %d' %
                                    (row_id, col_id))
                        n_missing += 1
                        if config.INGORE_DATA_MISMATCH:
                            data = ''
                    except KeyError:
                        log.warning('No key found in row %d column %d' %
                                    (row_id, col_id))
                        n_missing += 1
                        if config.INGORE_DATA_MISMATCH:
                            data = ''

                if is_custom_mm_type(data):
                    # explicit type
                    try:
                        self.grid_data[row_id][col_id] = data
                    except IndexError:
                        log.warning('No index found in row %d column %d' %
                                    (row_id, col_id))
                        n_missing += 1
                        if config.INGORE_DATA_MISMATCH:
                            data = ''
                else:
                    # wrap in type from headers
                    try:
                        self.grid_data[row_id][col_id] = field_type_class(data)
                    except IndexError:
                        log.warning('No index found in row %d column %d' %
                                    (row_id, col_id))
                        n_missing += 1
                        if config.INGORE_DATA_MISMATCH:
                            data = ''
        log.info("populated grid %sX%s" % (self.row_count, self.col_count))
        if n_missing > 0:
            log.info('%d missing items' % n_missing)
