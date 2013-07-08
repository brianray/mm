import unittest
import mm
import os
path = os.path.dirname(__file__)
no_django = True
try:
    os.environ['PYTHONPATH'] = path +':'+path + "/dummy_django_project"
    os.environ['DJANGO_SETTINGS_MODULE'] = 'dummy_django_project.settings'
    import django
    from dummy_django_project.marmir_test.models import TestAllBaseTypes
    from mm.contrib.django.data_model import DjangoDataModel
    from mm.contrib.django.grid import DjangoGrid
    no_django = False
except ImportError:
    print "could not import django"


class DjangoTestSuite(unittest.TestCase):

    def setUp(self):
        os.environ['PYTHONPATH'] = path +':'+path + "/dummy_django_project"
        if not no_django:
            from django.core import management
            management.call_command('syncdb', interactive=False, verbosity=0)

    def tearDown(self):
        os.unlink('marmir_django_test.sql')


    @unittest.skipIf(no_django, 'Skipping django test (django package not installed)')
    def test_custom_django_serializer(self):
        django_query_set = TestAllBaseTypes.objects.all()
        mm_doc = mm.Document(django_query_set, data_model_class=DjangoDataModel, grid_class=DjangoGrid)
        str = mm_doc.writestr()
        self.assertTrue(len(str) > 10,
            msg="String should be longer than %s" % len(str))
        f = open("test_django_serializer.xls", "wb")
        f.write(str)
        f.close()



if __name__ == "__main__":
    unittest.main()
