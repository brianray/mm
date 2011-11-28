from composer_base import ComposerBase
import lib.xlwt_0_7_2 as xlwt
import logging
import StringIO
import model_base


log = logging.getLogger(__name__)


class ComposerXLS(ComposerBase):


    def cell_to_value(self, cell):
        style = xlwt.XFStyle()
        if type(cell) == model_base.StringFieldType:

            return cell.data, style

        return "", style


    def write_cell(self, row_id, col_id, cell):
        
        value, style = self.cell_to_value(cell)
        self.sheet.write(col_id, row_id, value, style)


    def run(self):
           
        self.w = xlwt.Workbook()        
        self.sheet = self.w.add_sheet('sheet 1')
        self.iterate_grid()
        
        # write the file to string
        output = StringIO.StringIO() 
        self.w.save(output)
        contents = output.getvalue()
        output.close()

        return contents






