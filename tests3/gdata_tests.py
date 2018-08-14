import unittest
import getpass
import datetime
import mm
import os
from xlrd_helper import XLSReader
no_gdata = True
try:
    import gdata
    no_gdata = False
except ImportError:
    print("no gdata")


path = os.path.dirname(__file__)
now = datetime.datetime.now().replace(microsecond=0)
class TestGdataSuite(unittest.TestCase):

    
    @unittest.skipIf(no_gdata, 'Skipping gdata test (gdata package not installed)')
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

        # TODO: store this in a config
        username = input("Google Username: ")
        password = getpass.getpass("Google password: ")

        str = mm_doc.write_gdata(
                "Test MarMir File",
                username,
                password)

        # TODO: check if file actually got there or not




if __name__ == "__main__":
    unittest.main()
