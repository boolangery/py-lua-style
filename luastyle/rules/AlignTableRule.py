from luastyle import FormatterRule
import logging
import re


class AlignTableRule(FormatterRule):
    """
    This rule align lua table.
    """
    def apply(self, input):
        output = []
        level = 0

        p = re.compile(r'({(?:\\.|[^{}])*})', re.MULTILINE)

        match = p.findall(input)
        # for m in match:
            # print(m)
        # TODO
        return input
