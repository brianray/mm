import unittest
import datetime
import mm

class TestBasicSuite(unittest.TestCase):


    def Xtest_minimal(self):

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
        str = mm_doc.writestr()
        self.assertTrue(len(str) > 10, 
            msg="String should be longer than %s" % len(str))
        f = open("test_doc.xls", "wb")
        f.write(str)
        f.close()

    def test_simple_types(self):
        date = mm.Date(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%S%z")
        
    def test_mid_complex(self):

        my_data = [ 
            {
                'msg': "My first Cell",
                'id': 1,
                'when': mm.Date(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%S%z"),
            #    'homepage': mm.URL("https://github.com/brianray")
            },
            {
                'msg': "My second Cell",
                'id': 2,
                'when': datetime.datetime.now(),
                'homepage': mm.URL("http://twitter.com/brianray")
            },

        ]
        mm_doc = mm.Document(my_data)
        str = mm_doc.writestr()
        self.assertTrue(len(str) > 10, 
            msg="String should be longer than %s" % len(str))
        f = open("test_doc2.xls", "wb")
        f.write(str)
        f.close()



if __name__ == "__main__":
    unittest.main()
