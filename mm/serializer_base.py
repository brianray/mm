from grid_base import GridBase


class Serializer(object):
    """ Class that pairs data with models """
    def __init__(self, data_model, data):
        self.data = data
        self.data_model = data_model

    def serialize(self):
        """ returnes serialzed data into a Grid """
        grid = GridBase()

        # we care about order
        # that was set in model_base
        grid.row_count = len(self.data)
        field_headers =  self.data_model.field_headers
        grid.col_count = len(field_headers)
        grid.headers = field_headers 
        grid.populate(self.data)

        return grid

