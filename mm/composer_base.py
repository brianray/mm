
import logging

log = logging.getLogger(__name__)

class ComposerBase(object):
    """ Used by Composers """
    def run(self):
       raise Exception("Overwrite run() in subclass") 

    def __init__(self,data_model, grid):
        self.data_model = data_model
        self.grid = grid
        self.row_id = 0
        self.col_id = 0


    def iterate_grid(self):

        for row in self.grid.grid_data:
            self.col_id = 0
            for cell in row:
                self.write_cell(self.row_id, self.col_id, cell)
                self.col_id += 1
            self.row_id += 1




 

