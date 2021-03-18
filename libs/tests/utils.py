import unittest

from pyga import utils


class TestAnonymizeIp(unittest.TestCase):
    def test_with_no_ip(self):
        self.assertEqual("", utils.anonymize_ip(""))

    def test_with_valid_ip(self):
        self.assertEqual("1.2.3.0", utils.anonymize_ip("1.2.3.4"))
        self.assertEqual(
            "192.168.137.0", utils.anonymize_ip("192.168.137.123"))


if __name__ == '__main__':
    unittest.main()
