import unittest
from luastyle import rules
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:\t%(message)s')

class IndentRuleTestCase(unittest.TestCase):
    def setupTest(self, filePrefix, options=rules.IndentOptions()):
        self.maxDiff = None
        raw, exp = '', ''
        with open('./test_sources/' + filePrefix + '_raw.lua', 'r') as content_file:
            raw = content_file.read()
        with open('./test_sources/' + filePrefix + '_exp.lua', 'r') as content_file:
            exp = content_file.read()
        formatted = rules.IndentRule(options).apply(raw)
        print(formatted)
        self.assertEqual(formatted, exp)


    def test_no_indent(self):
        self.setupTest('no_indent')

    def test_for(self):
        self.setupTest('for')

    def test_do_end(self):
        self.setupTest('do_end')

    def test_continuation_line(self):
        self.setupTest('continuation_line')

    def test_continuation_line_func(self):
        self.setupTest('continuation_line_func')

    def test_function(self):
        self.setupTest('function')

    def test_nested_function(self):
        self.setupTest('nested_functions')

    def test_table(self):
        self.setupTest('table')

    def test_while(self):
        self.setupTest('while')

    def test_repeat(self):
        self.setupTest('repeat')

    def test_if_else(self):
        self.setupTest('if_else')

    def test_label(self):
        self.setupTest('label')

    def test_fornum(self):
        self.setupTest('fornum')

    def test_call(self):
        self.setupTest('call')

    def test_invoke(self):
        self.setupTest('invoke')

    def test_full_1(self):
        self.setupTest('full_1')

    def test_full_2(self):
        self.setupTest('full_2')

    def test_comments(self):
        self.setupTest('comments')

    def test_space_comma(self):
        self.setupTest('space_comma')
