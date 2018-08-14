import unittest
import datetime
import mm
import os
from xlrd_helper import XLSReader

path = os.path.dirname(__file__)
now = datetime.datetime.now().replace(microsecond=0)


class TestMultiSuite(unittest.TestCase):

    def test_minimal(self):

        my_data = [
            {
                'msg': "My first Cell",
                'id': 1,
                'when': now,
            },
            {
                'msg': "My second Cell",
                'id': 2,
                'when': now,
            },

        ]
        mm_doc = mm.Document(my_data)
        mm_doc.set_name("My Sheet 1")
        mm_child = mm.Document(my_data)
        mm_child.set_name("My Sheet 2")
        mm_doc.add_child(mm_child)
        str = mm_doc.writestr()
        self.assertTrue(
            len(str) > 10,
            msg="String should be longer than %s" % len(str))
        with open("tests/generated_files/test_multi.xls", "wb") as f:
            f.write(str)
        
        self.check("tests/generated_files/test_multi.xls", my_data)

    def check(self, filename, my_data):
        xls = XLSReader(filename)
        for worksheet_id in (0, 1):
            row = 0
            headers = []
            for ddict in my_data:
                col = 0
                for header, value in list(ddict.items()):
                    cell_type = xls.get_type(row, col, worksheet_idx=worksheet_id)
                    cell_value = xls.get_value(row, col, worksheet_idx=worksheet_id)
                    if row == 0:
                        #headers
                        headers.append(cell_value)
                    else:
                        column_header = headers[col]
                        data = my_data[row - 1]
                        self.assertEqual(cell_value, data[column_header])
                        self.assertEqual(cell_type, type(data[column_header]))

                    col += 1
                row += 1

if __name__ == "__main__":
    unittest.main()
