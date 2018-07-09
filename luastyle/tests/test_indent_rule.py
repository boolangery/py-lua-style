import unittest
import os
import textwrap
from luastyle import indenter
import logging
from luastyle.core import check_lua_bytecode

currdir = os.path.dirname(__file__)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:\t%(message)s')

class IndentRuleTestCase(unittest.TestCase):
    def setupTest(self, filePrefix, options=indenter.IndentOptions()):
        options.check_param_list = True
        options.if_cont_line_level = 2

        self.maxDiff = None
        raw, exp = '', ''
        with open(currdir + '/test_sources/' + filePrefix + '_raw.lua', 'r') as content_file:
            raw = content_file.read()
        with open(currdir + '/test_sources/' + filePrefix + '_exp.lua', 'r') as content_file:
            exp = content_file.read()
        formatted = indenter.IndentRule(options).apply(raw)
        print(formatted)
        self.assertEqual(formatted, exp)
        self.assertTrue(check_lua_bytecode(raw, formatted))

    def test_no_indent(self):
        self.setupTest('no_indent')

    def test_for(self):
        options = indenter.IndentOptions()
        options.space_around_op = True
        options.check_field_list = True
        self.setupTest('for', options)

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
        options = indenter.IndentOptions()
        options.check_field_list = True
        self.setupTest('table', options)

    def test_while(self):
        self.setupTest('while')

    def test_repeat(self):
        self.setupTest('repeat')

    def test_if_else(self):
        options = indenter.IndentOptions()
        options.space_around_op = True
        self.setupTest('if_else', options)

    def test_label(self):
        self.setupTest('label')

    def test_fornum(self):
        self.setupTest('fornum')

    def test_call(self):
        options = indenter.IndentOptions()
        options.space_around_op = True
        options.check_field_list = True
        self.setupTest('call', options)

    def test_invoke(self):
        self.setupTest('invoke')

    def test_full_1(self):
        options = indenter.IndentOptions()
        options.space_around_op = True
        options.check_field_list = True
        self.setupTest('full_1', options)

    def test_full_2(self):
        options = indenter.IndentOptions()
        options.space_around_op = True
        options.check_field_list = True
        self.setupTest('full_2', options)

    def test_comments(self):
        options = indenter.IndentOptions()
        options.space_around_op = True
        options.check_field_list = True
        self.setupTest('comments', options)

    def test_space_comma(self):
        options = indenter.IndentOptions()
        options.check_field_list = True
        self.setupTest('space_comma', options)

    def test_literal(self):
        self.setupTest('literal')

    def test_return(self):
        options = indenter.IndentOptions()
        self.setupTest('return', options)

    def test_return_1(self):
        options = indenter.IndentOptions()
        options.space_around_op = True
        self.setupTest('return_1', options)

    def test_chained_call(self):
        options = indenter.IndentOptions()
        options.space_around_op = True
        options.check_field_list = True
        self.setupTest('chained_call', options)

    def test_operators_check(self):
        options = indenter.IndentOptions()
        options.space_around_op = True
        self.setupTest('operators_check', options)

    def test_operators(self):
        self.setupTest('operators')

    def test_table_no_check(self):
        self.setupTest('table_no_check')

    def test_assign(self):
        self.setupTest('assign')

    def test_indent_size_option(self):
        src = textwrap.dedent('''\
            do
              local a
            end
            ''')
        expected = textwrap.dedent('''\
            do
                local a
            end
            ''')

        options = indenter.IndentOptions()
        options.indent_size = 2
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, src)

        options.indent_size = 4
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, expected)

    def test_func_cont_line_level_option(self):
        src = '''\
            function foo(a, b, 
            c, d)
            print(bar)
            end
            '''
        expected = textwrap.dedent('''\
            function foo(a, b, 
                  c, d)
              print(bar)
            end
            ''')

        options = indenter.IndentOptions()
        options.func_cont_line_level = 3
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, expected)

    def test_comment_options(self):
        src = '''\
            local foo --a comment
               --- a second comment
            -----a third comment
            -- a valid comment
            '''
        expected_1 = textwrap.dedent('''\
            local foo -- a comment
            --- a second comment
            ----- a third comment
            -- a valid comment
            ''')
        expected_3 = textwrap.dedent('''\
            local foo --   a comment
            ---   a second comment
            -----   a third comment
            --   a valid comment
            ''')

        options = indenter.IndentOptions()
        options.check_space_before_line_comment_text = True
        options.space_before_line_comment_text = 1
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, expected_1)

        options.space_before_line_comment_text = 3
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, expected_3)

    def test_space_around_assign_option(self):
        src = '''\
            local foo   =bar
            foo=    bar
            foo    =    {...}
            '''
        expected = textwrap.dedent('''\
            local foo = bar
            foo = bar
            foo = {...}
            ''')

        options = indenter.IndentOptions()
        options.space_around_assign = True
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, expected)

    def test_check_param_list_option(self):
        src = textwrap.dedent('''\
            local a  ,b  ,  c = 1,(2 + 3)   ,   foo(3)
            foo(a  ,  b,c,  d, e)
            function bar(a,b,    c,     d) end
            ''')
        expected = textwrap.dedent('''\
            local a, b, c = 1, (2 + 3), foo(3)
            foo(a, b, c, d, e)
            function bar(a, b, c, d) end
            ''')

        options = indenter.IndentOptions()
        options.check_param_list = False
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, src)

        options.check_param_list = True
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, expected)

    def test_check_field_list_option(self):
        src = textwrap.dedent('''\
            a = {1,2,    3    ,    4 , "foo"}
            foo {
              foo   = 42,
              bar   = 53,
              1,2,3   ,  4
            }
            ''')
        expected = textwrap.dedent('''\
            a = {1, 2, 3, 4, "foo"}
            foo {
              foo   = 42,
              bar   = 53,
              1, 2, 3, 4
            }
            ''')

        options = indenter.IndentOptions()
        options.check_field_list = False
        formatted = indenter.IndentRule(options).apply(src)
        print(formatted)
        self.assertEqual(formatted, src)

        options.check_field_list = True
        formatted = indenter.IndentRule(options).apply(src)
        print(formatted)
        self.assertEqual(formatted, expected)

    def test_skip_semi_colon_option(self):
        src = textwrap.dedent('''\
            print(a); print(b);
            ;
            local a = 42;;
            return 0;
            ''')
        expected = textwrap.dedent('''\
            print(a) print(b)
            local a = 42
            return 0
            ''')

        options = indenter.IndentOptions()
        options.skip_semi_colon = False
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, src)

        options.skip_semi_colon = True
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, expected)

    def test_if_cont_line_level_option(self):
        src = textwrap.dedent('''\
            if foo and
                bar or
                (1 + 2) then
              print(bar)
            elseif a and
                b then
              print(bar)
            end
            ''')
        expected = textwrap.dedent('''\
            if foo and
                    bar or
                    (1 + 2) then
              print(bar)
            elseif a and
                    b then
              print(bar)
            end
            ''')

        options = indenter.IndentOptions()
        options.if_cont_line_level = 2
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, src)

        options.if_cont_line_level = 4
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, expected)

    def test_break_if_statement_option(self):
        src = textwrap.dedent('''\
            if foo == nil then print(bar) elseif toto then else print(bar) end
            if log then log:notice("done") else return failure() end
            ''')
        expected = textwrap.dedent('''\
            if foo == nil then
              print(bar)
            elseif toto then
            else
              print(bar)
            end
            if log then
              log:notice("done")
            else
              return failure()
            end
            ''')

        options = indenter.IndentOptions()
        options.break_if_statement = False
        formatted = indenter.IndentRule(options).apply(src)
        self.assertEqual(formatted, src)

        options.break_if_statement = True
        formatted = indenter.IndentRule(options).apply(src)
        print(formatted)
        self.assertEqual(formatted, expected)

    def test_disable_table_with_comment(self):
        src = textwrap.dedent('''\
            local t = {
              -- @luastyle.disable
              1,    2,  4,
              8,    16, 32
            }
            ''')
        expected = textwrap.dedent('''\
            local t = {
              -- @luastyle.disable
              1,    2,  4,
              8,    16, 32
            }
            ''')

        options = indenter.IndentOptions()
        options.check_field_list = True
        formatted = indenter.IndentRule(options).apply(src)
        print(formatted)
        self.assertEqual(formatted, expected)

    #def test_smart_align_table(self):
    #    src = textwrap.dedent('''\
    #        local t = {
    #          1,    2,  4,
    #          8,    16, 32
    #        }
    #        ''')
    #    expected = textwrap.dedent('''\
    #        local t = {
    #          -- @luastyle.disable
    #          1,    2,  4,
    #          8,    16, 32
    #        }
    #        ''')

    #    options = indenter.IndentOptions()
    #    options.check_field_list = True
    #    formatted = indenter.IndentRule(options).apply(src)
    #    print(formatted)
    #    self.assertEqual(formatted, expected)

    def test_func_par(self):
        options = indenter.IndentOptions()
        options.force_func_call_space_checking = True
        options.func_call_space_n = 0
        self.setupTest('func_par', options)

    def test_break_for(self):
        options = indenter.IndentOptions()
        options.break_for_statement = True
        self.setupTest('break_for', options)

    def test_break_while(self):
        options = indenter.IndentOptions()
        options.break_while_statement = True
        self.setupTest('break_while', options)

    def test_ambiguous_with_skip_semi_colon_option(self):
        options = indenter.IndentOptions()
        options.skip_semi_colon = True
        self.setupTest('ambiguous', options)

    # #########################################################################
    # Continuous Integration Tests                                            #
    # #########################################################################
    def test_cont_int_1(self):
        self.setupTest('cont_int_1')
