class FormatterRule:
    def __init__(self):
        self._output = ''
    def apply(self, input):
        return input
    def revert(self, input):
        return input