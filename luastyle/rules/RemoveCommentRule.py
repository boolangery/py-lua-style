from luastyle import FormatterRule
import re
import logging

class RemoveCommentRule(FormatterRule):
    """
    This rule replace all comment in source code by placeholder.
    """
    def __init__(self):
        FormatterRule.__init__(self)
        self._comments = {}
        self._id = 1

    def apply(self, input):
        output = input
        # lua string regex:
        p = re.compile(r'--.*', re.MULTILINE)
        match = p.findall(output)
        for m in match:
            output = p.sub('___replaced_comment_' + str(self._id) + '___', output, 1)
            logging.debug('comment "' + m + '" replaced with id ' + str(self._id))
            self._comments[self._id] = m
            self._id += 1
        return output

    def revert(self, input):
        for k, v in self._comments.items():
            var = '___replaced_comment_' + str(k) + '___'
            input = input.replace(var, v)
            logging.debug('comment with id ' + str(k) + ' replaced with "' + v + '"')
        return input