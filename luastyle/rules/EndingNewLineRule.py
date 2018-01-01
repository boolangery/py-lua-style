from luastyle import FormatterRule
import logging


class EndingNewLineRule(FormatterRule):
    """
    This rule add the last new line if needed.
    """
    def apply(self, input):
        if input[-1] != '\n':
            input += '\n'
        return input
