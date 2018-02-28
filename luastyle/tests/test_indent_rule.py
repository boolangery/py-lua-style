import unittest
import os
from luastyle import indent
import logging

currdir = os.path.dirname(__file__)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:\t%(message)s')

class IndentRuleTestCase(unittest.TestCase):
    def setupTest(self, filePrefix, options=indent.IndentOptions()):
        options.comma_check = True
        options.space_around_op = True

        self.maxDiff = None
        raw, exp = '', ''
        with open(currdir + '/test_sources/' + filePrefix + '_raw.lua', 'r') as content_file:
            raw = content_file.read()
        with open(currdir + '/test_sources/' + filePrefix + '_exp.lua', 'r') as content_file:
            exp = content_file.read()
        formatted = indent.IndentRule(options).apply(raw)
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

    def test_literal(self):
        self.setupTest('literal')

    def test_return(self):
        options = indent.IndentOptions()
        options.indent_return_cont = True
        self.setupTest('return', options)

    def test_return_1(self):
        self.setupTest('return_1')

    def test_chained_call(self):
        self.setupTest('chained_call')

    def test_operators(self):
        self.setupTest('operators')

    def test_check_comments(self):
        options = indent.IndentOptions()
        options.check_space_before_line_comment = True
        options.space_before_line_comments = 2
        options.check_space_before_line_comment_text = True
        self.setupTest('check_comments', options)
