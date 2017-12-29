from luastyle import FormatterRule
import logging
import re


class IndentRule(FormatterRule):
    """
    This rule indent the code.
    """
    def __init__(self):
        FormatterRule.__init__(self)
        self.INDENT_KEYWORDS = ('function', 'if', 'repeat', 'while')
        self.INDENT_DELIM    = ('{', '(')
        self.DEDENT_KEYWORDS = ('end')
        self.DEDENT_DELIM    = ('}', ')')

    def apply(self, input):
        output = []
        level = 0

        for line in input.splitlines():
            tokens = re.findall('\W+', line)
            inc, dec = 0, 0
            previous = level
            for keyword in self.INDENT_KEYWORDS:
                inc += tokens.count(keyword)
            for keyword in self.INDENT_DELIM:
                inc += line.count(keyword)
            for keyword in self.DEDENT_KEYWORDS:
                dec += tokens.count(keyword)
            for keyword in self.DEDENT_DELIM:
                dec += line.count(keyword)

            diff = inc - dec
            level += diff

            logging.debug('indenting: ' + line)
            logging.debug('current level = ' + str(level))

            if diff == 0: # no diff, indent with current level
                newLine = ' ' * (level * 2) + line.strip()
            elif diff > 0: # level inc, indent on previous level
                newLine = ' ' * ((level - diff) * 2) + line.strip()
            else: # level dec, indent normal
                newLine = ' ' * ((level) * 2) + line.strip()
            output.append(newLine)
        return '\n'.join(map(str, output))