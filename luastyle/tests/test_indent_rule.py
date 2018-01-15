import unittest
import textwrap
from luastyle import rules
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:\t%(message)s')


WHITESPACE = 2

# contains all code sample used in test
CODE = {
    'no_indent': {
        'raw': "Account = {}",
        'exp': "Account = {}"
    },
    'for_loop': {
        'raw': textwrap.dedent("""
            for i,v in ipairs(t) do
            print(v)
            end
            """),
        'exp': textwrap.dedent("""
            for i,v in ipairs(t) do
              print(v)
            end
            """),
    },
    'do_end': {
        'raw': textwrap.dedent("""
            local v
            do
            local x = u2*v3-u3*v2
            local y = u3*v1-u1*v3
            local z = u1*v2-u2*v1
            v = {x,y,z}
            end
            """),
        'exp': textwrap.dedent("""
            local v
            do
              local x = u2*v3-u3*v2
              local y = u3*v1-u1*v3
              local z = u1*v2-u2*v1
              v = {x,y,z}
            end
            """)
    },
    'continuation_line': {
        'raw': textwrap.dedent("""
            longvarname = longvarname ..
            "Thanks for reading this example!"
            """),
        'exp': textwrap.dedent("""
            longvarname = longvarname ..
              "Thanks for reading this example!"
            """)
    },
    'continuation_line_func': {
        'raw': textwrap.dedent("""
            foo(bar, biz, "This is a long string...",
            baz, qux, "Lua")
            function foo(a, b, c, d,
            e, f, g, h)
            print('hello')
            end
            """),
        'exp': textwrap.dedent("""
            foo(bar, biz, "This is a long string...",
              baz, qux, "Lua")
            function foo(a, b, c, d,
                e, f, g, h)
              print('hello')
            end
            """)
    },
    'nested_functions': {
        'raw': textwrap.dedent("""
            local test = bind(function() end, function() end)
            
            callback(function(arg1)
            print(arg1)
            end)
            
            callback(function(arg1)
            print(arg1)
            end
            )
            """),
        'exp': textwrap.dedent("""
            local test = bind(function() end, function() end)
            
            callback(function(arg1)
                print(arg1)
              end)
            
            callback(function(arg1)
                print(arg1)
              end
            )
            """)
    },
    'table': {
        'raw': textwrap.dedent("""
            local table = {
            nested = {
            days = {
            monday = 1,
            tuesday = 2,
            },
            foo = 'bar',
            },
            non_nested = 42
            }
            local inline_table = {'1', '2', '3', '4'}
            local strange_table = {model = 'car',
            speed = 42.56, limit = 48,
            average = 12}
            """),
        'exp': textwrap.dedent("""
            local table = {
              nested = {
                days = {
                  monday = 1,
                  tuesday = 2,
                },
                foo = 'bar',
              },
              non_nested = 42
            }
            local inline_table = {'1', '2', '3', '4'}
            local strange_table = {model = 'car',
              speed = 42.56, limit = 48,
              average = 12}
            """)
    },
    'while': {
        'raw': textwrap.dedent("""
            while true do
                                     print(f)
              end
              while isValid() do print('ok'); process() end
            while a == 1 do
                print('equal') end
            """),
        'exp': textwrap.dedent("""
            while true do
              print(f)
            end
            while isValid() do print('ok'); process() end
            while a == 1 do
              print('equal') end
            """)
    },
    'do_end': {
        'raw': textwrap.dedent("""
            do
            local a
            -- comment
            end
            do local a end
            do do do local b end end end
            do
            local a
            do
            local b
            do
            local c = a + b
            end
            end
            end
            """),
        'exp': textwrap.dedent("""
            do
              local a
              -- comment
            end
            do local a end
            do do do local b end end end
            do
              local a
              do
                local b
                do
                  local c = a + b
                end
              end
            end
            """)
    },
    'repeat': {
        'raw': textwrap.dedent("""
            repeat
            line = os.read()
            until line ~= ""
            repeat print(foo) until isValid()
            repeat
            line = os.read() until line ~= ""
            """),
        'exp': textwrap.dedent("""
            repeat
              line = os.read()
            until line ~= ""
            repeat print(foo) until isValid()
            repeat
              line = os.read() until line ~= ""
            """)
    },
    'if_else': {
        'raw': textwrap.dedent("""
        if op == "+" then
        r = a + b
        elseif op == "-" then
        r = a - b
        elseif op == "*" then
        r = a*b
        elseif op == "/" then
        r = a/b
        else
        error("invalid operation")
        end
        if true then foo = 'bar' else foo = nil end
        if true then
        print('hello')
        end
        if true then
        print('hello') end
        if nested then
        if nested then
        if nested then print('ok Im nested') end
        elseif foo then
        local a = 42
        end
        end
        """),
        'exp': textwrap.dedent("""
        if op == "+" then
          r = a + b
        elseif op == "-" then
          r = a - b
        elseif op == "*" then
          r = a*b
        elseif op == "/" then
          r = a/b
        else
          error("invalid operation")
        end
        if true then foo = 'bar' else foo = nil end
        if true then
          print('hello')
        end
        if true then
          print('hello') end
        if nested then
          if nested then
            if nested then print('ok Im nested') end
          elseif foo then
            local a = 42
          end
        end
        """)
    },
}


class IndentRuleTestCase(unittest.TestCase):
    def test_no_indent(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['no_indent']['raw'])
        self.assertEqual(src, CODE['no_indent']['exp'])

    def test_for_indent(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['for_loop']['raw'])
        self.assertEqual(src, CODE['for_loop']['exp'])

    def test_continuation_line(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['continuation_line']['raw'])
        self.assertEqual(src, CODE['continuation_line']['exp'])

    def test_continuation_line_func(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['continuation_line_func']['raw'])
        self.assertEqual(src, CODE['continuation_line_func']['exp'])

    def test_nested_function(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['nested_functions']['raw'])
        self.assertEqual(src, CODE['nested_functions']['exp'])

    def test_table(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['table']['raw'])
        self.assertEqual(src, CODE['table']['exp'])

    def test_while(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['while']['raw'])
        self.assertEqual(src, CODE['while']['exp'])

    def test_do_end(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['do_end']['raw'])
        self.assertEqual(src, CODE['do_end']['exp'])

    def test_repeat(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['repeat']['raw'])
        self.assertEqual(src, CODE['repeat']['exp'])

    def test_if_else(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['if_else']['raw'])
        self.assertEqual(src, CODE['if_else']['exp'])
