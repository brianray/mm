import unittest
import datetime
import mm
import os
from xlrd_helper import XLSReader

path = os.path.dirname(__file__)
now = datetime.datetime.now().replace(microsecond=0)
class TestBasicSuite(unittest.TestCase):

    def test_minimal(self):

        my_data = [ 
            {
                'id dup': 2,
                'id': 1,
            },
            {
                'id dup': 4,
                'id': 3,
            },

        ]
        mm_doc = mm.Document(my_data)
        str = mm_doc.writestr()
        self.assertTrue(len(str) > 10, 
            msg="String should be longer than %s" % len(str))
        with open("tests/generated_files/test_dup.xls", "wb") as f:
            f.write(str)
    
        self.check("tests/generated_files/test_dup.xls", my_data)

    def check(self, filename, my_data):
        xls = XLSReader(filename)
        row = 0
        headers = []
        for ddict in my_data:
            col = 0
            for header, value in list(ddict.items()):
                cell_type = xls.get_type(row, col)
                cell_value = xls.get_value(row, col)
                if row == 0:
                   #headers
                   if cell_value in headers:
                       raise Exception("duplicate header %s" % cell_value)
                   headers.append(cell_value)
                else:
                   column_header = headers[col]
                   data = my_data[row-1]
                   self.assertEqual(cell_value, data[column_header])
                   self.assertEqual(cell_type, type(data[column_header]))

                col += 1
            row += 1
        



if __name__ == "__main__":
    unittest.main()
