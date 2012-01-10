import unittest
import datetime
import mm

class TestBasicSuite(unittest.TestCase):


    def test_minimal(self):

        my_data = [ 
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

        mm_doc = mm.Document(my_data)
        str = mm_doc.writestr()  #write("test.xls") 
        self.assertTrue(len(str) > 10, 
            msg="String should be longer than %s" % len(str))



