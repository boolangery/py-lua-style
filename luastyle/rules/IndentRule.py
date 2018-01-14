from luastyle import FormatterRule
import logging
from luaparser import asttokens
from luaparser import astnodes
from luaparser import ast
from luaparser.asttokens import Tokens

INDENT_TOKEN = [
    Tokens.WHILE,
    Tokens.REPEAT,
    Tokens.IF,
    Tokens.FOR,
    Tokens.FUNCTION,
    Tokens.BRACE_R,
    Tokens.PARENT_R]

DEDENT_TOKEN = [
    Tokens.END,
    Tokens.UNTIL,
    Tokens.BRACE_L,
    Tokens.PARENT_L]

DEDENT_LINE_TOKEN = [
    Tokens.ELSE,
    Tokens.ELSEIF]


class IndentVisitor(ast.ASTRecursiveVisitor):
    def __init__(self, atokens, indentValue):
        self._atokens = atokens
        self._indentValue = indentValue
        self._level = 0

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

    def indentNextLines(self, node):
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

    def enter_LocalAssign(self, node):
        atokens = self.tokens(node)
        lines = atokens.lines()
        lines[0].indent(self._level * self._indentValue)

        #self.stripTokens(atokens)

    def enter_Assign(self, node):
        if len(node.values)>0 and isinstance(node.values[0], astnodes.Concat):
            self.indentNextLines(node)

    def enter_Call(self, node):
        self._level += 1
        atokens = self.tokens(node)
        line  = atokens.first().lineNumber  # first line

        # indent arg on several lines
        for linetok in atokens.lines():
            if linetok.lineNumber > line:
                linetok.indent(self._level * self._indentValue)

        # if the last ')' is alone on the line then dedent
        last = atokens.last()
        if last.type == Tokens.PARENT_L.value:
            if len(last.line()) == 1 :
                last.line().indent((self._level - 1) * self._indentValue)

    def exit_Call(self, node):
        self._level -= 1

    def enter_Function(self, node):
        self._level += 1
        atokens = self.tokens(node)
        line  = atokens.first().lineNumber             # first line

        # grab all tokens representing function args
        argstok = atokens.nextOfType(Tokens.PARENT_R).grabUntil(Tokens.PARENT_L)
        # indent argument on several lines
        for linetok in argstok.lines():
            if linetok.lineNumber > line:
                linetok.indent((self._level + 1) * self._indentValue)

        # indent body if not inline
        for n in node.body:
            bodytok = self.tokens(n)
            for linetok in bodytok.lines():
                if linetok.lineNumber > line:
                    linetok.indent(self._level * self._indentValue)

        # dedent end if first token on line
        endl = atokens.last().line()
        if endl.first() == atokens.last():
            endl.indent((self._level - 1) * self._indentValue)

    def exit_Function(self, node):
        self._level -= 1

    def enter_Forin(self, node):
        self._level += 1

        # indent body
        for n in node.body:
            bodytok = self.tokens(n)
            for linetok in bodytok.lines():
                linetok.indent(self._level * self._indentValue)

    def exit_Forin(self, node):
        self._level -= 1

    def enter_If(self, node):
        atokens = self.tokens(node)
        level = atokens.first().column      # current indentation level
        line  = atokens.first().lineNumber  # first line

        # indent body
        for n in node.body:
            bodytok = self.tokens(n)
            for linetok in bodytok.lines():
                linetok.indent(level + self._indentValue)

        # indent orelse
        if isinstance(node.orelse, list):
            for n in node.orelse:
                bodytok = self.tokens(n)
                for linetok in bodytok.lines():
                    linetok.indent(level + self._indentValue)


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

        # try to get AST tree, do nothing if invalid source code is provided
        try:
            tree = ast.parse(input)
        except ast.SyntaxException as e:
            logging.error(str(e))
            return input

        # strip left all
        for aline in atokens.lines():
            aline.stripl()

        IndentVisitor(atokens, self.indentValue).visit(tree)

        # simply return modified tokens to source
        return atokens.toSource()


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

        IndentVisitor(atokens, self.indentValue).visit(tree)

        # simply return modified tokens to source
        return atokens.toSource()
