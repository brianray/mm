#!/usr/bin/python

import datetime
import unittest
import mm

now = datetime.datetime.now().replace(microsecond=0)

class TestFormula(unittest.TestCase):
    def test_simple_formula(self):
        my_data = [ 
            {
                'msg': "My first Row",
                'id': 1,
                'when': now,
            },
            {
                'msg': "My second Row",
                'id': 2,
                'when': now,
            },
            {
                'msg': "The total",
                'id': mm.Formula("SUM(C2:C3)"),
                'when': now,
                },
        ]

        mm_doc = mm.Document(my_data)
        mm_doc.write("example_formula.xls")

if __name__ == "__main__":
    unittest.main()
