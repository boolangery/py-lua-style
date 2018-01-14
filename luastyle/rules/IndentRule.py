from luastyle import FormatterRule
import logging
from luaparser import asttokens
from luaparser import ast
from luaparser import astnodes
from luaparser.asttokens import Tokens

INDENT_TOKEN = [
    Tokens.WHILE,
    Tokens.REPEAT,
    Tokens.IF,
    Tokens.FOR,
    Tokens.FUNCTION,
    Tokens.BRACE_R]

DEDENT_TOKEN = [
    Tokens.END,
    Tokens.UNTIL,
    Tokens.BRACE_L]

DEDENT_LINE_TOKEN = [
    Tokens.ELSE,
    Tokens.ELSEIF]


class IndentVisitor(ast.ASTVisitor):
    def __init__(self, atokens, indentValue):
        self._atokens = atokens
        self._indentValue = indentValue

    def tokens(self, node):
        return self._atokens.fromAST(node)

    def stripTokens(self, atokens, allowedWs=1):
        """Remove inter-token non needed whitespace"""
        for ltokens in atokens.lines():
            for i in range(0, len(ltokens)-1):
                wsToRemove = ltokens[i+1].column - (ltokens[i].column + len(ltokens[i].text)) - allowedWs
                if wsToRemove > 0:
                    ltokens[i+1].column = ltokens[i+1].column - wsToRemove
                    logging.debug('removing whitespace beetween "' + ltokens[i].text + '" and "' + ltokens[i+1].text + '"')

    def visit_LocalAssign(self, node):
        atokens = self.tokens(node)
        self.stripTokens(atokens)

    def visit_Assign(self, node):
        if len(node.values)>0 and isinstance(node.values[0], astnodes.Concat):

            atokens = self.tokens(node)
            if atokens.lineCount() > 0:
                firstLine = True
                level = 0
                for ltokens in atokens.lines():
                    if len(ltokens) > 0:
                        if firstLine:
                            level = ltokens.first().column
                            firstLine = False
                        else:
                            ltokens.indent(level + self._indentValue)

class IndentRule(FormatterRule):
    """
    This rule indent the code.
    """
    def __init__(self, indentValue):
        FormatterRule.__init__(self)
        self.indentValue = indentValue

    def apply(self, input):
        atokens = asttokens.parse(input)
        tree = None

        # try to get AST tree, do nothing if invalid source
        # code is provided
        try:
            tree = ast.parse(input)
        except ast.SyntaxError as e:
            logging.error(str(e))
            return input

        # strip left all
        for line in atokens.lines():
            line.stripl()

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

        # extra rules
        IndentVisitor(atokens, self.indentValue).visit(tree)

        # simply return modified tokens to source
        return atokens.toSource()
