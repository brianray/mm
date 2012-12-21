import unittest
import core


class test_font_data(unittest.TestCase):

    def test_checkwidth1(self):

        width = core.get_string_width('Arial', 11, 'hello world') 
        self.assertEqual(width, 52.421875)

    def test_checkwidth2(self):
        width = core.get_string_width('Times New Roman', 23 ,'The quick brown fox jumps over the lazy dog')
        self.assertEqual(width, 420.46875)




