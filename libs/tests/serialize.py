import unittest

try:
    import cPickle as pickle
except ImportError as e:
    import pickle


class TestSerialize(unittest.TestCase):

    def test_unique_id_must_be_equals(self):
        """
        This will test if the unique_id is equals after deserialization
        even if it is not acessed before serialization
        """
        from pyga.requests import Visitor

        visitor = Visitor()
        serialized_visitor = pickle.dumps(visitor)
        deserialized_visitor = pickle.loads(serialized_visitor)
        self.assertEqual(visitor.unique_id, deserialized_visitor.unique_id)
