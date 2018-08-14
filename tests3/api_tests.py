import unittest
import datetime
import mm

class ApiTestSuite(unittest.TestCase):

    def test_simple_types(self):
        date = mm.Date(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%S")
         


if __name__ == "__main__":
    unittest.main()
