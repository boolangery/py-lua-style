from luastyle import FormatterRule
import logging
import re


class IndentRule(FormatterRule):
    """
    This rule indent the code.
    """
    def __init__(self):
        FormatterRule.__init__(self)
        self.INDENT_KEYWORDS = ['function', 'if', 'repeat', 'while', 'for']
        self.INDENT_DELIM    = ['{', '(']
        self.DEDENT_KEYWORDS = ['end']
        self.DEDENT_DELIM    = ['}', ')']
        self.DEDENT_LINE     = ['else', 'elseif']

    def apply(self, input):
        output = []
        level = 0

        for line in input.splitlines():
            tokens = re.split(r'[{}\(\)\[\],=:\.;,\s]\s*', line)
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
            dedentLine = False
            for keyword in self.DEDENT_LINE:
                if tokens.count(keyword) > 0:
                    dedentLine = True
                    break

            diff = inc - dec
            level += diff
            if dedentLine:
                lineLevel -= 1
            else:
                lineLevel = level

            logging.debug('indenting: ' + line)
            logging.debug('current level = ' + str(level))

            if diff == 0: # no diff, indent with current level
                newLine = ' ' * (lineLevel * 2) + line.strip()
            elif diff > 0: # level inc, indent on previous level
                newLine = ' ' * ((lineLevel - diff) * 2) + line.strip()
            else: # level dec, indent normal
                newLine = ' ' * ((lineLevel) * 2) + line.strip()
            output.append(newLine)
        return '\n'.join(map(str, output))