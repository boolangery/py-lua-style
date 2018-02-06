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

        self.checkSpaceAfterComma = True

class IndentVisitor(ast.ASTRecursiveVisitor):
    def __init__(self, options):
        self._options = options
        self._level = 0

    def currentIndent(self, offset = 0):
        return (self._level + offset) * self._options.indentSize

    def enter_Chunk(self, node):
        pass

    def isConcatAssign(self, node):
        return (node.values and not (
                isinstance(node.values[0], astnodes.AnonymousFunction) or
                isinstance(node.values[0], astnodes.Table)))

    def enter_LocalAssign(self, node):
        if self.isConcatAssign(node):
            logging.debug('LocalAssign is a concat assign: ' + node.edit().toSource())
            self._level += self._options.assignContinuationLineLevel

        editor = node.edit()
        first = editor.first()
        for line in editor.lines():
            if line.lineNumber > first.lineNumber:
                line.indent(self.currentIndent())

    def exit_LocalAssign(self, node):
        if self.isConcatAssign(node):
            self._level -= self._options.assignContinuationLineLevel

    def enter_Assign(self, node):
        if self.isConcatAssign(node):
            self._level += self._options.assignContinuationLineLevel

        editor = node.edit()
        first = editor.first()
        for line in editor.lines():
            if line.lineNumber > first.lineNumber:
                line.indent(self.currentIndent())

    def exit_Assign(self, node):
        if self.isConcatAssign(node):
            self._level -= self._options.assignContinuationLineLevel


    def enter_While(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())

    def exit_While(self, node):
        self._level -= 1

    def enter_Do(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())

    def exit_Do(self, node):
        self._level -= 1

    def enter_Repeat(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())

    def exit_Repeat(self, node):
        self._level -= 1

    def enter_Function(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())
        node.args.edit().indent(self.currentIndent(self._options.functionContinuationLineLevel - 1))

    def exit_Function(self, node):
        self._level -= 1

    def enter_LocalFunction(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())
        node.args.edit().indent(self.currentIndent(self._options.functionContinuationLineLevel - 1))

    def exit_LocalFunction(self, node):
        self._level -= 1

    def enter_Method(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())

    def exit_Method(self, node):
        self._level -= 1

    def enter_AnonymousFunction(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())

    def exit_AnonymousFunction(self, node):
        self._level -= 1

    def enter_Forin(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())

    def exit_Forin(self, node):
        self._level -= 1

    def enter_If(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())

        # indent orelse body
        if node.orelse and not isinstance(node.orelse, astnodes.ElseIf):
            node.orelse.edit().indent(self.currentIndent())

    def exit_If(self, node):
        self._level -= 1

    def enter_ElseIf(self, node):
        node.body.edit().indent(self.currentIndent())

        # indent orelse body
        if node.orelse and not isinstance(node.orelse, astnodes.ElseIf):
            node.orelse.edit().indent(self.currentIndent())

    def enter_Fornum(self, node):
        self._level += 1
        node.body.edit().indent(self.currentIndent())


    def exit_Fornum(self, node):
        self._level -= 1

    def isClassicCall(self, node):
        """Return true is its a call with parenthesis."""
        first = node.args.edit().first()
        if first:
            prev = first.prev()
            if prev:
                return prev.type == Tokens.OPAR.value
        return False

    def enter_Call(self, node):
        if self.isClassicCall(node):
            self._level += 1
        node.args.edit().indent(self.currentIndent())

    def exit_Call(self, node):
        if self.isClassicCall(node):
            self._level -= 1
        editor = node.edit()

        # the rule for indenting the last line containing CPAR:
        # indent on same level as call opening OPAR if
        # the CPAR is the first token on line or if previous token
        # is a [CBRACE, END]
        closingParen = editor.lastOfType(Tokens.CPAR)
        if closingParen:
            prev = closingParen.prev()
            if prev and prev.type in [Tokens.CBRACE.value, Tokens.END.value]:
                if prev.isFirstOnLine():
                    closingParen.line().indent(self.currentIndent())

    def enter_Invoke(self, node):
        node.args.edit().indent(self.currentIndent(1))

    def exit_Invoke(self, node):
        pass

    def enter_Table(self, node):
        self._level += 1
        editor = node.edit()
        editor.indent(self.currentIndent())

        # opening brace
        openingBrace = editor.first()
        if openingBrace.isFirstOnLine():
            openingBrace.line().indent(self.currentIndent(-1))

    def exit_Table(self, node):
        self._level -= 1
        editor = node.edit()
        closingBrace = editor.lastOfType(Tokens.CBRACE)
        if closingBrace.isFirstOnLine():
            closingBrace.line().indent(self.currentIndent())

CHECK_SPACE_AFTER_COMMA_IF_NOT_IN = [
    Tokens.NEWLINE.value
]

class IndentRule(FormatterRule):
    """
    This rule indent the code.
    """
    def __init__(self, options):
        FormatterRule.__init__(self)
        self._options = options

    def apply(self, input):
        # strip
        output = []
        for line in input.splitlines():
            output.append(line.strip())
        input = '\n'.join(map(str, output)) + '\n'

        tree = None

        # try to get AST tree, do nothing if invalid source code is provided
        try:
            tree = ast.parse(input)
        except ast.SyntaxException as e:
            logging.error(str(e))
            return input

        # indent
        IndentVisitor(self._options).visit(tree)

        # check SPACE after comma
        if self._options.checkSpaceAfterComma:
            for t in tree.edit():
                if t.type == Tokens.COMMA.value:
                    next = t.next([])  # no ignore
                    if next:
                        if next.type == Tokens.SPACE.value:
                            next.text = ' '
                        elif next.type not in CHECK_SPACE_AFTER_COMMA_IF_NOT_IN:
                            t.insertRight(Tokens.SPACE, ' ')

        # simply return modified tokens to source
        return tree.edit().allToSource()
