import logging
from luaparser import ast, astnodes
from luaparser.asttokens import Tokens
from enum import Enum

class FormatterRule:
    def __init__(self):
        self._output = ''
    def apply(self, input):
        return input
    def revert(self, input):
        return input


class IndentOptions():
    def __init__(self):
        self.indent_size = 2
        self.indent_char = ' '
        self.indent_with_tabs = False
        self.initial_indent_level = 0

        self.assign_cont_line_level = 1
        self.func_cont_line_level = 2
        self.comma_check = False


class IndentVisitor(ast.ASTRecursiveVisitor):
    def __init__(self, options):
        self._options = options
        self._level = 0

    def currentIndent(self, offset=0):
        if not self._options.indent_with_tabs:
            return (self._level + offset + self._options.initial_indent_level) * self._options.indent_size
        else:
            return self._level + offset + self._options.initial_indent_level

    def indentLine(self, line, offset=0):
        if not self._options.indent_with_tabs:
            line.indent(self.currentIndent(offset), self._options.indent_char)
        else:
            line.indent(self.currentIndent(offset), '\t')

    def indentLines(self, node, offset=0):
        for line in node.edit().lines():
            first = line.first()
            if first:
                if first.isFirstOnLine():
                    if not self._options.indent_with_tabs:
                        line.indent(self.currentIndent(offset), self._options.indent_char)
                    else:
                        line.indent(self.currentIndent(offset), '\t')

    def enter_Chunk(self, node):
        pass

    def enter_Block(self, node):
        self.indentLines(node)

    def indentAssign(self, node):
        """Check if we need to indent this assignment.

        Rules to indent are:
            * At least one value and first value type is a Concat
            * Several values

        """
        return (node.values and type(node.values[0]) in [
            astnodes.Concat
        ]) or len(node.values) > 1

    def enter_Assign(self, node):
        if self.indentAssign(node):
            logging.debug('Assign is a concat assign: ' + node.edit().toSource())
            self._level += self._options.assign_cont_line_level

        editor = node.edit()
        first = editor.first()
        for line in editor.lines():
            if line.lineNumber > first.lineNumber:
                self.indentLine(line)

    def exit_Assign(self, node):
        if self.indentAssign(node):
            self._level -= self._options.assign_cont_line_level

    def enter_While(self, node):
        self._level += 1

    def exit_While(self, node):
        self._level -= 1

    def enter_Do(self, node):
        self._level += 1

    def exit_Do(self, node):
        self._level -= 1

    def enter_Repeat(self, node):
        self._level += 1

    def exit_Repeat(self, node):
        self._level -= 1

    def enter_Function(self, node):
        self._level += 1
        self.indentLines(node.args, self._options.func_cont_line_level - 1)

    def exit_Function(self, node):
        self._level -= 1

    def enter_LocalFunction(self, node):
        self._level += 1
        self.indentLines(node.args, self._options.func_cont_line_level - 1)

    def exit_LocalFunction(self, node):
        self._level -= 1

    def enter_Method(self, node):
        self._level += 1

    def exit_Method(self, node):
        self._level -= 1

    def enter_AnonymousFunction(self, node):
        self._level += 1

    def exit_AnonymousFunction(self, node):
        self._level -= 1

    def enter_Forin(self, node):
        self._level += 1

    def exit_Forin(self, node):
        self._level -= 1

    def enter_If(self, node):
        self._level += 1

    def exit_If(self, node):
        self._level -= 1

    def enter_ElseIf(self, node):
        pass

    def enter_Fornum(self, node):
        self._level += 1

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

    def callIndentLast(self, node, type):
        # the rule for indenting the last line containing CPAR:
        # indent on same level as call opening OPAR if
        # the CPAR is the first token on line or if previous token
        # is a [CBRACE, END]
        editor = node.edit()
        closingParen = editor.lastOfType(type)
        if closingParen:
            prev = closingParen.prev()
            if prev and prev.type in [Tokens.CBRACE.value, Tokens.END.value]:
                if prev.isFirstOnLine():
                    self.indentLine(closingParen.line())

    def enter_Call(self, node):
        if self.isClassicCall(node):
            self._level += 1
        self.indentLines(node.args)

    def exit_Call(self, node):
        if self.isClassicCall(node):
            self._level -= 1
        self.callIndentLast(node, Tokens.CPAR)

    def enter_Invoke(self, node):
        if self.isClassicCall(node):
            self._level += 1
        self.indentLines(node.args)

    def exit_Invoke(self, node):
        if self.isClassicCall(node):
            self._level -= 1
        self.callIndentLast(node, Tokens.CPAR)

    def enter_Table(self, node):
        self._level += 1
        editor = node.edit()
        self.indentLines(node)

        # opening brace
        openingBrace = editor.first()
        if openingBrace.isFirstOnLine():
            self.indentLine(openingBrace.line(), -1)

    def exit_Table(self, node):
        self._level -= 1

        closingBrace = node.edit().lastOfType(Tokens.CBRACE)
        if closingBrace.isFirstOnLine():
            self.indentLine(closingBrace.line())

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
        # try to get AST tree, do nothing if invalid source code is provided
        try:
            tree = ast.parse(input)
        except ast.SyntaxException as e:
            logging.error(str(e))
            return input

        # indent
        IndentVisitor(self._options).visit(tree)

        # check SPACE after comma
        if self._options.comma_check:
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
