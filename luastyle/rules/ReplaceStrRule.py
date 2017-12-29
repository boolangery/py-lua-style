from luastyle import FormatterRule
import re
import logging

class ReplaceStrRule(FormatterRule):
    """
    This rule replace all string in source code by placeholder.
    """
    def __init__(self):
        FormatterRule.__init__(self)
        self._strings = {}
        self._id = 1

    def apply(self, input):
        output = input
        # lua string regex:
        p1 = re.compile(r'((?:\"|\')(?:\\.|[^\"\\\'])*(?:\"|\'))', re.MULTILINE)
        p2 = re.compile(r'(\[=*\[[\S\s]*\]=*\])', re.MULTILINE)

        match = p2.findall(output)
        for m in match:
            output = p2.sub('___replaced_str_' + str(self._id) + '___', output, 1)
            logging.debug('string "' + m + '" replaced with id ' + str(self._id))
            self._strings[self._id] = m # cache replaced string
            self._id += 1
        match = p1.findall(output)
        for m in match:
            output = p1.sub('___replaced_str_' + str(self._id) + '___', output, 1)
            logging.debug('string "' + m + '" replaced with id ' + str(self._id))
            self._strings[self._id] = m # cache replaced string
            self._id += 1
        return output

    def revert(self, input):
        for k, v in self._strings.items():
            var = '___replaced_str_' + str(k) + '___'
            input = input.replace(var, v)
            logging.debug('string with id ' + str(k) + ' replaced with "' + v + '"')
        return input