import xlrd
from datetime import datetime

class XLSReader:

    def __init__(self, file):
        workbook = xlrd.open_workbook(file)
        self.book = workbook
        self.worksheets = [workbook.sheet_by_name(x) for x in workbook.sheet_names()]

        # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
        self.cell_types = {
            '1':str,
            '2':int,
            '3':datetime
        }

    def get_type(self, row, colm):
        worksheet = self.worksheets[0]
        return self.cell_types[str(worksheet.cell_type(row, colm))]

    def get_value(self, row, colm):
        worksheet = self.worksheets[0]
        
        val =  worksheet.cell_value(row, colm)
        cell_type = self.get_type(row, colm)
        if cell_type == datetime:
            return datetime(*xlrd.xldate_as_tuple(val, self.book.datemode))
        return val

