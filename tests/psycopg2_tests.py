import unittest
import mm
import os
from xlrd_helper import XLSReader
path = os.path.dirname(__file__)
no_psycopg = True
try:
    import psycopg2
    import psycopg2.extras
    no_psycopg = False
except ImportError:
    print "could not import psycopg2"


class PsycopgTestSuite(unittest.TestCase):

    def setUp(self):
        self.conn = psycopg2.connect("dbname='template1' user='testuser' host='localhost' password='password'")
        dict_cur = self.conn.cursor()
        dict_cur.execute("CREATE TABLE marmir_test (num INT, data CHAR(12))")
        dict_cur.close()

    def tearDown(self):
        dict_cur = self.conn.cursor()
        dict_cur.execute("DROP TABLE marmir_test;")
        dict_cur.close()

    def test_psycopg(self):

        if no_psycopg:
            print 'Skipping psycopg2 test (psycopg2 package not installed)'
            return

        dict_cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        dict_cur.execute("INSERT INTO marmir_test (num, data) VALUES(%s, %s)",
                         (100, "abc'def"))
        dict_cur.execute("INSERT INTO marmir_test (num, data) VALUES(%s, %s)",
                         (200, "mmmmaaarrrr"))
        dict_cur.execute("SELECT * FROM marmir_test")
        my_data = dict_cur.fetchall()
        dict_cur.close()

        mm_doc = mm.Document(my_data)
        str = mm_doc.writestr()
        self.assertTrue(
            len(str) > 10,
            msg="String should be longer than %s" % len(str))
        f = open("test_psycopg.xls", "wb")
        f.write(str)
        f.close()
        self.check("test_psycopg.xls", my_data)

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
