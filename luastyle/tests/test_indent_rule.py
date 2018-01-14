import unittest
import textwrap
from luastyle import rules

WHITESPACE = 2

# contains all code sample used in test
CODE = {
    'no_indent': {
        'raw': "Account = {}",
        'exp': "Account = {}"
    },
    'for_indent': {
        'raw': textwrap.dedent("""
            for i,v in ipairs(t) do
            if type(v) == "string" then
            print(v)
            end
            end
            """),
        'exp': textwrap.dedent("""
            for i,v in ipairs(t) do
              if type(v) == "string" then
                print(v)
              end
            end
            """),
    }
}


class IndentRuleTestCase(unittest.TestCase):
    def test_no_indent(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['no_indent']['raw'])
        self.assertEqual(src, CODE['no_indent']['exp'])

    def test_for_indent(self):
        src = rules.IndentRule(WHITESPACE).apply(CODE['for_indent']['raw'])
        print(src)
        self.assertEqual(src, CODE['for_indent']['exp'])
