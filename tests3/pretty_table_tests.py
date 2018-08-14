import unittest
import datetime
import mm
no_pretty_table = True
try:
    import prettytable  # NOQA
    from mm.contrib.prettytable.composers import ComposerPrettyTable

    no_pretty_table = False
except ImportError:
    print("could not import pretty_table")

now = datetime.datetime.now().replace(microsecond=0)


class PrettyTableTestSuite(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skipIf(no_pretty_table, 'Skipping PrettyTable test (prettytable package not installed)')
    def test_custom_pretty_table_serializer(self):

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
        mm_doc = mm.Document(my_data)  # data_model_class=PrettyTableModel)
        mm_doc.set_composer_class(ComposerPrettyTable)
        out = '''
+----------------+---------------------+----+
|      msg       |         when        | id |
+----------------+---------------------+----+
| My first Cell  | %(now)s | 1  |
| My second Cell | %(now)s | 2  |
+----------------+---------------------+----+''' % dict(now=now)
        self.assertEqual(str(mm_doc.writestr()), out.strip())


if __name__ == "__main__":
    unittest.main()
