import unittest
import datetime
import mm
import os

path = os.path.dirname(__file__)

class CustomTestSuite(unittest.TestCase):

    def setUp(self):
        self.my_data = [ 
            {
                'msg': "My first Cell",
                'id': 1,
                'when': datetime.datetime.now(),
            },
            {
                'msg': "My second Cell",
                'id': 2,
                'when': datetime.datetime.now(),
            },

        ]

    def test_no_header_row(self):
        
        config = { 
            'headers': False,
            'freeze_row': 0
        }

        mm_doc = mm.Document(self.my_data, config_dict=config)
        str = mm_doc.writestr()
        self.assertTrue(len(str) > 10, 
            msg="String should be longer than %s" % len(str))
        with open("tests/generated_files/test_custom_no_header.xls", "wb") as f:
            f.write(str)
        


    def test_no_style(self):
        
        config = { 
            'header_style': '',
            'row_styles': ()
        }

        mm_doc = mm.Document(self.my_data, config_dict=config)
        str = mm_doc.writestr()
        self.assertTrue(len(str) > 10, 
            msg="String should be longer than %s" % len(str))
        with open("tests/generated_files/test_custom_no_styles.xls", "wb") as f:
            f.write(str)
        


    def test_row_style(self):
        
        config = { 
            'row_styles': ( "font-family: Times-New-Roman;",)
        }

        mm_doc = mm.Document(self.my_data, config_dict=config)
        str = mm_doc.writestr()
        self.assertTrue(len(str) > 10, 
            msg="String should be longer than %s" % len(str))
        with open("tests/generated_files/test_custom_row_styles.xls", "wb") as f:
            f.write(str)
        

        
if __name__ == "__main__":
    unittest.main()
