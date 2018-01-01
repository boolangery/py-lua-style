from luastyle import FormatterRule
import logging


class StripRule(FormatterRule):
    """
    This rule stip whitespace.
    """
    def apply(self, input):
        output = []
        for line in input.splitlines():
            output.append(line.rstrip())
        return '\n'.join(map(str, output))