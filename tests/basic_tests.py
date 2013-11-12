import unittest
import datetime
import mm
import os
import filecmp
from xlrd_helper import XLSReader
from mm.config_base import ConfigBase
path = os.path.dirname(__file__)
now = datetime.datetime.now().replace(microsecond=0)


class TestBasicSuite(unittest.TestCase):

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
        str = mm_doc.writestr()
        self.assertTrue(
            len(str) > 10,
            msg="String should be longer than %s" % len(str))
        f = open("test_doc.xls", "wb")
        f.write(str)
        f.close()
        self.check("test_doc.xls", my_data)

    def test_minimal_lists(self):

        my_headers = ('id', 'msg', 'when')
        my_data = (
            (1, "my first row", now),
            (2, "my second row", now),
        )

        mm_doc = mm.Document(my_data, order=my_headers)
        str = mm_doc.writestr()
        self.assertTrue(
            len(str) > 10,
            msg="String should be longer than %s" % len(str))
        f = open("test_list_doc.xls", "wb")
        f.write(str)
        f.close()
        as_dict = [dict(zip(my_headers, row)) for row in my_data]
        self.check("test_list_doc.xls", as_dict)

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

    def test_mid_complex(self):

        my_data = [
            {
                'msg': "My first Cell",
                'id': 1,
                'when': mm.Date(now, "%Y-%m-%dT%H:%M:%S"),
                'homepage': mm.URL("https://github.com/brianray")
            },
            {
                'msg': "My second Cell",
                'id': 2,
                'when': now,
                'homepage': mm.URL("http://twitter.com/brianray",
                                   "Tweet Tweet")
            },

        ]
        mm_doc = mm.Document(my_data)
        str = mm_doc.writestr()
        self.assertTrue(
            len(str) > 10,
            msg="String should be longer than %s" % len(str))
        f = open("test_doc2.xls", "wb")
        f.write(str)
        f.close()

        #TODO self.check("test_doc2.xls", my_data)

    def test_image(self):

        my_data = [
            {
                'profile': mm.Image(os.path.join(path, "author.bmp"), 230, 326)
            },
        ]
        mm_doc = mm.Document(my_data)
        str = mm_doc.writestr()
        self.assertTrue(
            len(str) > 10,
            msg="String should be longer than %s" % len(str))
        f = open("test_doc_image.xls", "wb")
        f.write(str)

    def test_col_type(self):

        my_data = [
            {
                'date': "2003-01-01"
            },
        ]
        col_types = {'date': mm.Date}
        mm_doc = mm.Document(my_data, column_types=col_types)
        str = mm_doc.writestr()
        self.assertTrue(
            len(str) > 10,
            msg="String should be longer than %s" % len(str))
        f = open("test_col_types.xls", "wb")
        f.write(str)

    def test_missing_1(self):
        my_data = [
            {
                'msg': "My first Cell",
                'id': 1,
                'when': now,
            },
            {
                'msg': "My second Cell has missing data",
                'id': 2,
            },

        ]
        mm_doc = mm.Document(my_data)
        str = mm_doc.writestr()
        self.assertTrue(
            len(str) > 10,
            msg="String should be longer than %s" % len(str))
        f = open("test_doc.xls", "wb")
        f.write(str)
        f.close()
        self.check("test_doc.xls", my_data)

    def test_missing_2(self):
        my_data = [
            {
                'msg': "My first Cell",
                'id': 1,
            },
            {
                'msg': "My second Cell",
                'id': 2,
            },
            {
                'msg': "My third Cell has missing data",
                'id': 3,
                'when': now,
            },
        ]
        with self.assertRaises(Exception):
            mm_doc = mm.Document(my_data)
            str = mm_doc.writestr()
            self.assertTrue(
                len(str) > 10,
                msg="String should be longer than %s" % len(str))
            f = open("test_doc.xls", "wb")
            f.write(str)
            f.close()
            self.check("test_doc.xls", my_data)
    
    def test_write_and_writestr_binary_output(self):
        """
        write() and writestr() should generate the same files
        """
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
        
        # Write using write()
        mm_doc = mm.Document(my_data)
        mm_doc.write('test_file1.xls')

        # Write using writestr() in binary mode
        str = mm_doc.writestr()
        with open('test_file2.xls', 'wb') as f:
            f.write(str)

        self.assertTrue(filecmp.cmp('test_file1.xls', 'test_file2.xls'))

if __name__ == "__main__":
    unittest.main()
