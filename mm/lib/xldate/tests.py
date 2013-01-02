import unittest
import convert


class TestsConvert(unittest.TestCase):

    def test_formats(self):
        tests = (
            ("%b %d %H:%M:%S %Y", "mmm dd hh:mm:ss yyyy"), # Jul 08 08:08:10 2011
            ('%b|%B|%c|%d|%f|%H|%m|%M|%p|%S|%x|%X|%y|%Y|%%','mmm|mmmm|M/D/YY h:mm:ss|dd|[ss].00|hh|mm|mm|AM/PM|ss|M/D/YY|h:mm:ss|yy|yyyy|\%'),
        )
        for test in tests:
            excel = convert.to_excel_from_C_codes(test[0],{})
            self.assertEqual(test[1], excel)


        tests = (
            ('%a', '%A', '%I', '%j', '%U', '%w', '%W', '%z', '%Z',)
        )
        for test in tests:
            self.assertRaises(convert.UnsupportedFormatCodeException, 
                                 convert.to_excel_from_C_codes, test, {})

if __name__ == "__main__":
    unittest.main()


