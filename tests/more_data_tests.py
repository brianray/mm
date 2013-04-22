import unittest
import datetime
import mm
import os
from decimal import Decimal

from xlrd_helper import XLSReader

path = os.path.dirname(__file__)
now = datetime.datetime.now().replace(microsecond=0)


class TestMoreDataSuite(unittest.TestCase):

    def test_minimal(self):

        my_data = [
            {
                'none type': None,
                'Bool True': True,
                'Bool False': False,
                'Decimal': Decimal("3.14"),
            },

        ]
        mm_doc = mm.Document(my_data)
        str = mm_doc.writestr()
        self.assertTrue(
            len(str) > 10,
            msg="String should be longer than %s" % len(str))
        f = open("test_multi_data.xls", "wb")
        f.write(str)
        f.close()
        self.check("test_multi_data.xls", my_data)

    def check(self, filename, my_data):
        xls = XLSReader(filename)
        row = 0
        headers = []
        for ddict in my_data:
            col = 0
            for header, value in ddict.items():
                cell_type = xls.get_type(row, col)
                cell_value = xls.get_value(row, col)
                if row == 0:
                    #headers
                    headers.append(cell_value)
                else:
                    column_header = headers[col]
                    data = my_data[row - 1]
                    self.assertEquals(cell_value, data[column_header])
                    self.assertEquals(cell_type, type(data[column_header]))

                col += 1
            row += 1

if __name__ == "__main__":
    unittest.main()
