from luastyle import FormatterRule
import logging
from luaparser import asttokens
from luaparser.asttokens import Tokens

INDENT_TOKEN = [
    Tokens.DO,
    Tokens.WHILE,
    Tokens.REPEAT,
    Tokens.IF,
    Tokens.FOR,
    Tokens.FUNCTION,
    Tokens.BRACE_R]

DEDENT_TOKEN = [
    Tokens.END,
    Tokens.UNTIL,
    Tokens.THEN,
    Tokens.BRACE_L]

DEDENT_LINE_TOKEN = [
    Tokens.ELSE,
    Tokens.ELSEIF]

class IndentRule(FormatterRule):
    """
    This rule indent the code.
    """
    def __init__(self, indentValue):
        FormatterRule.__init__(self)
        self.indentValue = indentValue

    def apply(self, input):
        atokens = asttokens.parse(input)
        level = 0

        # here simply count token that indent or dedent code
        for line in atokens.lines():
            inc, dec = 0, 0
            inc += len(line.types(INDENT_TOKEN))
            dec += len(line.types(DEDENT_TOKEN))

            # check if this line only need dedent (elseif, else..)
            dedentLine = (len(line.types(DEDENT_LINE_TOKEN)) > 0)

            # compute indentation level
            diff = inc - dec
            level += diff # global level

            # line level
            if dedentLine:  lineLevel -= 1
            else:           lineLevel = level

            logging.debug('level=' + str(level) + '\tinc=' + str(inc) + '\tdec= ' + str(dec) + '\t' + line.toSource())

            # level inc, indent on previous level
            if diff > 0:
                line.indent((lineLevel - diff) * self.indentValue)
            else:
                line.indent(lineLevel * self.indentValue)

        # simply return modified tokens to source
        return atokens.toSource()
