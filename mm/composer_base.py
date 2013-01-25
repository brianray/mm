
import logging
from model_base import HeaderFieldType

log = logging.getLogger(__name__)

class ComposerBase(object):
    """ Used by Composers """
    def run(self):
       raise Exception("Overwrite run() in subclass") 

    def __init__(self,data_model, grid, document):
        self.data_model = data_model
        self.grid = grid
        self.document = document
        self.row_id = 0
        self.col_id = 0


    def iterate_grid(self):

        for row in self.grid.grid_data:
            self.col_id = 0
            self.start_new_row(self.row_id)
            for cell in row:
                self.write_cell(self.row_id, self.col_id, cell)
                self.col_id += 1
            self.end_row(self.row_id)
            self.row_id += 1

        

    def write_header(self):
        i = 0
        for header in self.data_model.field_titles:
            cell = HeaderFieldType(data=header)
            log.info(cell.__dict__)
            self.write_cell(0, i, cell)
            i += 1
        self.row_id += 1



    def finish(self):
        """ Things we do after we are done """
        for key in [x for x in dir(self.document.config) if not x.startswith("_") ]:
            self.set_option(key)




