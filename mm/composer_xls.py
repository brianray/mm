from composer_base import ComposerBase
import lib.xlwt_0_7_2 as xlwt
import logging
import StringIO
import model_base


log = logging.getLogger(__name__)


class ComposerXLS(ComposerBase):

    def cell_to_value(self, cell):
        style = xlwt.XFStyle()
        
        if type(cell) == model_base.HeaderFieldType:
            return cell.data, style

        elif type(cell) == model_base.StringFieldType:
            return cell.data, style
        
        return "", style


    def write_cell(self, row_id, col_id, cell):
        
        value, style = self.cell_to_value(cell)
        self.sheet.write(row_id, col_id, value, style)


    def set_option(self, key):
       
        val = getattr(self.document.config,key)
        if key == 'freeze_col' and val and val >0:
            self.sheet.panes_frozen = True
            self.sheet.vert_split_pos = val
         
        elif key == 'freeze_row' and val and val >0:
            self.sheet.panes_frozen = True
            self.sheet.horz_split_pos = val

        else:

            log.info("Nothing to be done for %s" % key) 
    
            return
        log.info("Set option %s" % key) 



    def run(self):
           
        self.w = xlwt.Workbook()        
        self.sheet = self.w.add_sheet('Sheet 1')
        if self.document.config.headers:
            self.write_header()
        self.iterate_grid()
        self.finish()       
         
        # write the file to string
        output = StringIO.StringIO() 
        self.w.save(output)
        contents = output.getvalue()
        output.close()

        return contents






