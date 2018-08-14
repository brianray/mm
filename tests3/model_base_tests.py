import unittest
import mm.model_base as model_base

class ModelBaseSuite(unittest.TestCase):


    def test_get_member_listl(self):
        list = model_base.get_members_list()
        self.assertIn(model_base.IntFieldType, list)


if __name__ == "__main__":
    unittest.main()
