from luastyle import FormatterRule
import logging
from luaparser import asttokens
from luaparser import astnodes
from luaparser import ast
from luaparser.asttokens import Tokens
from enum import Enum

class IndentType(Enum):
    SPACE = 1

class IndentOptions():
    def __init__(self):
        self.indentType = IndentType.SPACE
        self.indentSize = 2
        self.assignContinuationLineLevel = 1
        self.functionContinuationLineLevel = 2

class IndentVisitor(ast.ASTRecursiveVisitor):
    def __init__(self, atokens, options):
        self._atokens = atokens
        self._options = options
        self._level = 0

    def currentIndent(self, offset = 0):
        return (self._level + offset) * self._options.indentSize

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

    def indentBody(self, node):
        atokens = self.tokens(node)
        line = atokens.first().lineNumber
        for n in node.body:
            nodetok = self.tokens(n)
            for linetok in nodetok.lines():
                if linetok.lineNumber > line:
                    linetok.indent(self.currentIndent())

    def smartIndent(self, node, startType):
        atokens = self.tokens(node)
        firsttok = atokens[0]
        if firsttok.type != startType.value:
            firsttok = firsttok.nextOfType(startType)

        lasttok = atokens[-1]
        nodetok = self.tokens(node)[1:-1]
        for linetok in nodetok.lines():
            if (linetok.lineNumber > firsttok.lineNumber) and (linetok.lineNumber < lasttok.lineNumber):
                linetok.indent(self.currentIndent())

    def enter_LocalAssign(self, node):
        pass
        # atokens = self.tokens(node)
        # lines = atokens.lines()
        # lines[0].indent(self.currentIndent())

    def enter_Assign(self, node):
        if len(node.values)>0 and isinstance(node.values[0], astnodes.Concat):
            atokens = self.tokens(node)
            for linetok in atokens.lines()[1:]:
                linetok.indent(self.currentIndent(1))

    def enter_While(self, node):
        self._level += 1
        self.indentBody(node)

    def exit_While(self, node):
        self._level -= 1

    def enter_Do(self, node):
        self._level += 1
        self.smartIndent(node, Tokens.DO)

    def exit_Do(self, node):
        self._level -= 1

    def enter_Repeat(self, node):
        self._level += 1
        self.indentBody(node)

    def exit_Repeat(self, node):
        self._level -= 1

    def enter_Function(self, node):
        self._level += 1
        atokens = self.tokens(node)
        line  = atokens.first().lineNumber

        # grab all tokens representing function args
        argstok = atokens.first().nextOfType(Tokens.PARENT_R).grabUntil(Tokens.PARENT_L)
        # indent argument on several lines
        for linetok in argstok.lines():
            if linetok.lineNumber > line:
                linetok.indent(self.currentIndent(1))

        # indent body if not inline
        for n in node.body:
            bodytok = self.tokens(n)
            for linetok in bodytok.lines():
                if linetok.lineNumber > line:
                    linetok.indent(self.currentIndent())

        # dedent end if first token on line
        endl = atokens.last().line()
        if endl.first() == atokens.last():
            endl.indent(self.currentIndent(-1))

    def exit_Function(self, node):
        self._level -= 1

    def enter_Forin(self, node):
        self._level += 1
        self.smartIndent(node, Tokens.DO)

        # indent body
        #for n in node.body:
        #    bodytok = self.tokens(n)
        #    for linetok in bodytok.lines():
        #        linetok.indent(self.currentIndent())

    def exit_Forin(self, node):
        self._level -= 1

    def enter_If(self, node):
        self._level += 1
        atokens = self.tokens(node)
        line  = atokens.first().lineNumber  # first line

        # indent body
        for n in node.body:
            bodytok = self.tokens(n)
            for linetok in bodytok.lines():
                if linetok.lineNumber > line:
                    linetok.indent(self.currentIndent())

        # indent orelse
        if isinstance(node.orelse, list):
            for n in node.orelse:
                bodytok = self.tokens(n)
                for linetok in bodytok.lines():
                    if linetok.lineNumber > line:
                        linetok.indent(self.currentIndent())

    def exit_If(self, node):
        self._level -= 1

    def enter_ElseIf(self, node):
        atokens = self.tokens(node)
        line  = atokens.first().lineNumber  # first line

        # indent body
        for n in node.body:
            bodytok = self.tokens(n)
            for linetok in bodytok.lines():
                if linetok.lineNumber > line:
                    linetok.indent(self.currentIndent())

        # indent orelse
        if isinstance(node.orelse, list):
            for n in node.orelse:
                bodytok = self.tokens(n)
                for linetok in bodytok.lines():
                    if linetok.lineNumber > line:
                        linetok.indent(self.currentIndent())

    def enter_Fornum(self, node):
        self._level += 1
        # self.indentBody(node)
        self.smartIndent(node, Tokens.DO)

    def exit_Fornum(self, node):
        self._level -= 1

    def enter_Call(self, node):
        self._level += 1
        atokens = self.tokens(node)
        line  = atokens.first().lineNumber  # first line

        # indent arg on several lines
        for linetok in atokens.lines():
            if linetok.lineNumber > line:
                linetok.indent(self.currentIndent())

        # if the last ')' is alone on the line then dedent
        last = atokens.last()
        if last.type == Tokens.PARENT_L.value:
            if len(last.line()) == 1 :
                last.line().indent(self.currentIndent(-1))

    def exit_Call(self, node):
        self._level -= 1

    def enter_Invoke(self, node):
        self._level += 1
        atokens = self.tokens(node)
        line  = atokens.first().lineNumber  # first line

        # indent arg on several lines
        for linetok in atokens.lines():
            if linetok.lineNumber > line:
                linetok.indent(self.currentIndent())

        # if the last ')' is alone on the line then dedent
        last = atokens.last()
        if last.type == Tokens.PARENT_L.value:
            if len(last.line()) == 1 :
                last.line().indent(self.currentIndent(-1))

    def exit_Invoke(self, node):
        self._level -= 1

    def enter_Table(self, node):
        self._level += 1
        atokens = self.tokens(node)

        # indent table body, skip first line
        for linetok in atokens.lines()[1:]:
            linetok.indent(self.currentIndent())

        # dedent '}' if no other table token before
        brackettok = atokens.last()
        if brackettok.isFirstOnLine():
            brackettok.line().indent(self.currentIndent(-1))

    def exit_Table(self, node):
        self._level -= 1


class IndentRule(FormatterRule):
    """
    This rule indent the code.
    """
    def __init__(self, options):
        FormatterRule.__init__(self)
        self._options = options

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

        IndentVisitor(atokens, self._options).visit(tree)

        # simply return modified tokens to source
        return atokens.toSource()
