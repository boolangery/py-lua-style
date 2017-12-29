from luastyle import FormatterRule
import logging

class IndentRule(FormatterRule):
    """
    This rule indent the code.
    """
    def __init__(self):
        FormatterRule.__init__(self)
        self.INDENT_KEYWORDS = ('function', 'if', 'repeat', 'while', '{', '(')
        self.DEDENT_KEYWORDS = ('end', '}', ')')

    def apply(self, input):
        output = []
        level = 0

        for line in input.splitlines():
            inc, dec = 0, 0
            previous = level
            for keyword in self.INDENT_KEYWORDS:
                inc += line.count(keyword)
            for keyword in self.DEDENT_KEYWORDS:
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