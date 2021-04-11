# -*- coding: utf-8 -*-
from enzyme.parsers import ebml
import io
import os.path
import requests
import unittest
import yaml
import zipfile


# Test directory
TEST_DIR = os.path.join(os.path.dirname(__file__), os.path.splitext(__file__)[0])

# EBML validation directory
EBML_VALIDATION_DIR = os.path.join(os.path.dirname(__file__), 'parsers', 'ebml')


def setUpModule():
    if not os.path.exists(TEST_DIR):
        r = requests.get('http://downloads.sourceforge.net/project/matroska/test_files/matroska_test_w1_1.zip')
        with zipfile.ZipFile(io.BytesIO(r.content), 'r') as f:
            f.extractall(TEST_DIR)


class EBMLTestCase(unittest.TestCase):
    def setUp(self):
        self.stream = io.open(os.path.join(TEST_DIR, 'test1.mkv'), 'rb')
        with io.open(os.path.join(EBML_VALIDATION_DIR, 'test1.mkv.yml'), 'r') as yml:
            self.validation = yaml.safe_load(yml)
        self.specs = ebml.get_matroska_specs()

    def tearDown(self):
        self.stream.close()

    def check_element(self, element_id, element_type, element_name, element_level, element_position, element_size, element_data, element,
                      ignore_element_types=None, ignore_element_names=None, max_level=None):
        """Recursively check an element"""
        # base
        self.assertTrue(element.id == element_id)
        self.assertTrue(element.type == element_type)
        self.assertTrue(element.name == element_name)
        self.assertTrue(element.level == element_level)
        self.assertTrue(element.position == element_position)
        self.assertTrue(element.size == element_size)
        # Element
        if not isinstance(element_data, list):
            self.assertTrue(type(element) == ebml.Element)
            if element_type != ebml.BINARY:
                self.assertTrue(element.data == element_data)
            return
        # MasterElement
        if ignore_element_types is not None:  # filter validation on element types
            element_data = [e for e in element_data if e[1] not in ignore_element_types]
        if ignore_element_names is not None:  # filter validation on element names
            element_data = [e for e in element_data if e[2] not in ignore_element_names]
        if element.level == max_level:  # special check when maximum level is reached
            self.assertTrue(element.data is None)
            return
        self.assertTrue(len(element.data) == len(element_data))
        for i in range(len(element.data)):
            self.check_element(element_data[i][0], element_data[i][1], element_data[i][2], element_data[i][3],
                               element_data[i][4], element_data[i][5], element_data[i][6], element.data[i], ignore_element_types,
                               ignore_element_names, max_level)

    def test_parse_full(self):
        result = ebml.parse(self.stream, self.specs)
        self.assertTrue(len(result) == len(self.validation))
        for i in range(len(self.validation)):
            self.check_element(self.validation[i][0], self.validation[i][1], self.validation[i][2], self.validation[i][3],
                               self.validation[i][4], self.validation[i][5], self.validation[i][6], result[i])

    def test_parse_ignore_element_types(self):
        ignore_element_types = [ebml.INTEGER, ebml.BINARY]
        result = ebml.parse(self.stream, self.specs, ignore_element_types=ignore_element_types)
        self.validation = [e for e in self.validation if e[1] not in ignore_element_types]
        self.assertTrue(len(result) == len(self.validation))
        for i in range(len(self.validation)):
            self.check_element(self.validation[i][0], self.validation[i][1], self.validation[i][2], self.validation[i][3],
                               self.validation[i][4], self.validation[i][5], self.validation[i][6], result[i], ignore_element_types=ignore_element_types)

    def test_parse_ignore_element_names(self):
        ignore_element_names = ['EBML', 'SimpleBlock']
        result = ebml.parse(self.stream, self.specs, ignore_element_names=ignore_element_names)
        self.validation = [e for e in self.validation if e[2] not in ignore_element_names]
        self.assertTrue(len(result) == len(self.validation))
        for i in range(len(self.validation)):
            self.check_element(self.validation[i][0], self.validation[i][1], self.validation[i][2], self.validation[i][3],
                               self.validation[i][4], self.validation[i][5], self.validation[i][6], result[i], ignore_element_names=ignore_element_names)

    def test_parse_max_level(self):
        max_level = 3
        result = ebml.parse(self.stream, self.specs, max_level=max_level)
        self.validation = [e for e in self.validation if e[3] <= max_level]
        self.assertTrue(len(result) == len(self.validation))
        for i in range(len(self.validation)):
            self.check_element(self.validation[i][0], self.validation[i][1], self.validation[i][2], self.validation[i][3],
                               self.validation[i][4], self.validation[i][5], self.validation[i][6], result[i], max_level=max_level)


def generate_yml(filename, specs):
    """Generate  a validation file for the test video"""
    def _to_builtin(elements):
        """Recursively convert elements to built-in types"""
        result = []
        for e in elements:
            if isinstance(e, ebml.MasterElement):
                result.append((e.id, e.type, e.name, e.level, e.position, e.size, _to_builtin(e.data)))
            else:
                result.append((e.id, e.type, e.name, e.level, e.position, e.size, None if isinstance(e.data, io.BytesIO) else e.data))
        return result
    video = io.open(os.path.join(TEST_DIR, filename), 'rb')
    yml = io.open(os.path.join(EBML_VALIDATION_DIR, filename + '.yml'), 'w')
    yaml.safe_dump(_to_builtin(ebml.parse(video, specs)), yml)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(EBMLTestCase))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
