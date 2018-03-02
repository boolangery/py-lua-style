import logging
from luaparser import ast, astnodes
from luaparser.asttokens import Tokens
from enum import Enum

class FormatterRule:
    def __init__(self):
        self._output = ''

    def apply(self, source):
        return source

    def revert(self, source):
        return source


class IndentOptions:
    def __init__(self):
        self.indent_size = 2
        self.indent_char = ' '
        self.indent_with_tabs = False
        self.initial_indent_level = 0

        self.assign_cont_line_level = 1
        self.func_cont_line_level = 2
        self.comma_check = False
        self.indent_return_cont = False
        self.space_around_op = False

        self.check_space_before_line_comment = False
        self.space_before_line_comments = 1
        self.check_space_before_line_comment_text = False
        self.space_before_line_comment_text = 1


IGNORE = [Tokens.SPACE, Tokens.NEWLINE, Tokens.SHEBANG, Tokens.LINE_COMMENT, Tokens.COMMENT]
IGNORE_COMMENTS = [Tokens.SHEBANG, Tokens.LINE_COMMENT, Tokens.COMMENT]

class Modes(Enum):
    NESTED = 1


class IndentVisitor:
    def __init__(self, options):
        self._options = options
        self._level = 0
        self._is_nested = False
        # _modes contains a dictionary of flags associated to
        # a counter. The counter is incremented on flag enter, and
        # decreased on flag leave
        self._modes = {}

    def enter_mode(self, mode):
        if mode in self._modes:
            self._modes[mode] += 1
        else:
            self._modes[mode] = 1
        return self._modes[mode] == 1  # return True if entered for first time

    def leave_mode(self, mode):
        self._modes[mode] -= 1
        return self._modes[mode] == 0  # return True if leaving mode

    def get_modes(self):
        return [mode for mode in self._modes.keys() if self._modes[mode] > 0]

    def inc_level(self, n=1):
        self._level += n

    def dec_level(self, n=1):
        self._level -= n

    def inc_level_if(self, condition, n=1):
        if condition:
            self._level += n

    def dec_level_if(self, condition, n=1):
        if condition:
            self._level -= n

    def visit(self, node):
        if node is None: return
        if isinstance(node, astnodes.Node):
            # call enter node method
            # if no visitor method found for this arg type,
            # search in parent arg type:
            parentType = node.__class__
            while parentType != object:
                name = 'visit_' + parentType.__name__
                visitor = getattr(self, name, None)
                if visitor:
                    visitor(node)
                    break
                else:
                    parentType = parentType.__bases__[0]

        elif isinstance(node, list):
            for n in node:
                self.visit(n)

    def get_current_indent(self, offset=0):
        if not self._options.indent_with_tabs:
            return (self._level + offset + self._options.initial_indent_level) * self._options.indent_size
        else:
            return self._level + offset + self._options.initial_indent_level

    def indent_line(self, line, offset=0):
        if not self._options.indent_with_tabs:
            line.indent(self.get_current_indent(offset), self._options.indent_char)
        else:
            line.indent(self.get_current_indent(offset), '\t')

    def indent_lines(self, node, offset=0):
        for line in node.edit().lines():
            first = line.first()
            if first:
                if first.isFirstOnLine():
                    if not self._options.indent_with_tabs:
                        line.indent(self.get_current_indent(offset), self._options.indent_char)
                    else:
                        line.indent(self.get_current_indent(offset), '\t')

    def visit_Chunk(self, node):
        self.visit(node.body)

    # ####################################################################### #
    # Root Nodes                                                              #
    # ####################################################################### #
    def visit_Block(self, node):
        self.indent_lines(node)  # useful to indent comments in first level
        self.visit(node.body)

    def visit_Node(self, node):
        self.indent_lines(node)

    # ####################################################################### #
    # Assignments                                                             #
    # ####################################################################### #
    def indent_assign(self, node):
        """Check if we need to indent this assignment.

        Rules to indent are:
            * At least one value and first value type is a Concat
            * Several values

        """
        return (node.values and type(node.values[0]) in [
            astnodes.Concat
        ]) or len(node.values) > 1

    def visit_Assign(self, node):
        self.visit(node.targets)
        indent_cont = self.indent_assign(node)
        self.inc_level_if(indent_cont, self._options.assign_cont_line_level)
        self.visit(node.values)
        self.dec_level_if(indent_cont, self._options.assign_cont_line_level)

    # ####################################################################### #
    # Control Structures                                                      #
    # ####################################################################### #
    def visit_While(self, node):
        self.visit(node.test)
        self.inc_level()
        self.visit(node.body)
        self.dec_level()

    def visit_Do(self, node):
        self.inc_level()
        self.visit(node.body)
        self.dec_level()

    def visit_Repeat(self, node):
        self.inc_level()
        self.visit(node.body)
        self.dec_level()
        self.visit(node.test)

    def visit_Forin(self, node):
        self.visit(node.iter)
        self.visit(node.targets)
        self.inc_level()
        self.visit(node.body)
        self.dec_level()

    def visit_Fornum(self, node):
        self.visit(node.target)
        self.visit(node.start)
        self.visit(node.stop)
        self.visit(node.step)
        self.inc_level()
        self.visit(node.body)
        self.dec_level()

    def visit_If(self, node):
        self.inc_level()
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)
        self.dec_level()

    def visit_ElseIf(self, node):
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)

    # ####################################################################### #
    # Call / Invoke / Method / Anonymous                                      #
    # ####################################################################### #
    def visit_Function(self, node):
        self.indent_lines(node)  # handle comments
        self.inc_level(self._options.func_cont_line_level)
        self.visit(node.args)
        self.dec_level(self._options.func_cont_line_level)

        self.inc_level()
        self.visit(node.body)
        self.dec_level()

    def visit_LocalFunction(self, node):
        self.indent_lines(node)  # handle comments
        self.inc_level(self._options.func_cont_line_level)
        self.visit(node.args)
        self.dec_level(self._options.func_cont_line_level)

        self.inc_level()
        self.visit(node.body)
        self.dec_level()

    def visit_Method(self, node):
        self.indent_lines(node)  # handle comments
        self.inc_level(self._options.func_cont_line_level)
        self.visit(node.args)
        self.dec_level(self._options.func_cont_line_level)

        self.inc_level()
        self.visit(node.body)
        self.dec_level()

    def visit_AnonymousFunction(self, node):
        self.indent_lines(node)  # handle comments
        self.inc_level(self._options.func_cont_line_level)
        self.visit(node.args)
        self.dec_level(self._options.func_cont_line_level)

        self.inc_level()
        self.visit(node.body)
        self.dec_level()
        self.indent_last_if_first(node, Tokens.END)

    def is_call_with_opar(self, node):
        """Return true is its a call with parenthesis."""
        first = node.args.edit().first()
        if first:
            prev = first.prev()
            if prev:
                return prev.type == Tokens.OPAR.value
        return False

    def indent_last_if_first(self, node, type):
        # the rule for indenting the last line containing CPAR:
        # indent on same level as call opening OPAR if
        # the CPAR is the first token on line or if previous token
        # is a [CBRACE, END]
        editor = node.edit()
        lasttok = editor.lastOfType(type)

        if lasttok:
            prev = lasttok.prev()
            if prev and prev.type in [Tokens.CBRACE.value, Tokens.END.value]:
                if prev.isFirstOnLine():
                    self.indent_line(lasttok.line())
            elif lasttok.isFirstOnLine():
                self.indent_line(lasttok.line())

    def visit_Index(self, node):
        self.visit(node.value)
        self.visit(node.idx)

    def visit_Call(self, node):
        has_parenthesis = self.is_call_with_opar(node)

        editor = node.func.edit()
        is_splitted = editor.first(IGNORE).lineNumber < editor.last(IGNORE).lineNumber

        self.visit(node.func)

        if is_splitted:
            self.inc_level_if(self.enter_mode(Modes.NESTED))
            self.indent_line(editor.last(IGNORE).line())

        self.inc_level_if(has_parenthesis)
        self.visit(node.args)
        self.dec_level_if(has_parenthesis)

        if is_splitted:
            self.dec_level_if(self.leave_mode(Modes.NESTED))
        if has_parenthesis:
            self.indent_last_if_first(node, Tokens.CPAR)

    def visit_Invoke(self, node):
        has_parenthesis = self.is_call_with_opar(node)
        func_token = node.func.edit().first(IGNORE)
        source_token = node.source.edit().first(IGNORE)
        is_splitted = func_token.lineNumber > source_token.lineNumber

        self.visit(node.source)
        self.visit(node.func)

        if is_splitted:
            self.inc_level_if(is_splitted)
        self.visit(node.func)

        if is_splitted:
            self.indent_line(node.func.edit().first().line())
        self.inc_level_if(has_parenthesis)
        self.visit(node.args)
        self.dec_level_if(has_parenthesis)

        if has_parenthesis:
            self.indent_last_if_first(node, Tokens.CPAR)

        if is_splitted:
            self.dec_level_if(is_splitted)

    # ####################################################################### #
    # Operators                                                               #
    # ####################################################################### #
    def visit_BinaryOp(self, node):
        self.indent_lines(node)  # indent lines starting with operator
        self.visit(node.left)
        self.visit(node.right)

        # check there is one whitespace around operator token
        if self._options.space_around_op:
            operator_token = node.right.edit().first(IGNORE).prev()
            tok_left = operator_token.prev(IGNORE_COMMENTS)
            tok_right = operator_token.next(IGNORE_COMMENTS)

            # handle the case where we are at the start of a new line
            if not tok_left.prev(IGNORE_COMMENTS).type == Tokens.NEWLINE.value:
                if tok_left.type == Tokens.SPACE.value:
                    tok_left.text = ' '
                else:
                    operator_token.insertLeft(Tokens.SPACE, ' ')
            if not tok_right.type == Tokens.NEWLINE.value:
                if tok_right.type == Tokens.SPACE.value:
                    tok_right.text = ' '
                else:
                    operator_token.insertRight(Tokens.SPACE, ' ')

    # ####################################################################### #
    # Types and Values                                                        #
    # ####################################################################### #
    def visit_Table(self, node):
        editor = node.edit()
        o_brace = editor.firstOfType(Tokens.OBRACE)
        if o_brace.isFirstOnLine():
            self.indent_line(o_brace.line())

        self.inc_level()
        for key in node.keys:
            self.indent_lines(key)  # indent key line
            self.visit(key)
        for value in node.values:
            self.visit(value)
        self.dec_level()

        c_brace = editor.lastOfType(Tokens.CBRACE)
        if c_brace.isFirstOnLine():
            self.indent_line(c_brace.line())

    def visit_Return(self, node):
        if self._options.indent_return_cont:
            self.inc_level()
        self.visit(node.values)
        if self._options.indent_return_cont:
            self.dec_level()


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

    def check_comma(self, tokens):
        """
        If comma_check check option is enabled,
        ensure that each comma is followed by a space.
        """
        if self._options.comma_check:
            for t in tokens:
                if t.type == Tokens.COMMA.value:
                    next = t.next([])  # no ignore
                    if next:
                        if next.type == Tokens.SPACE.value:
                            next.text = ' '
                        elif next.type not in CHECK_SPACE_AFTER_COMMA_IF_NOT_IN:
                            t.insertRight(Tokens.SPACE, ' ')

    def check_line_comments(self, tokens):
        def do_check(t):
            if t.type == Tokens.LINE_COMMENT.value:
                if self._options.check_space_before_line_comment:
                    # check space before comment opening
                    # if the comment is not alone on the line
                    if not t.isFirstOnLine():
                        prevtok = t.prev([])  # no ignore
                        if prevtok.type == Tokens.SPACE.value:
                            prevtok.text = ' ' * self._options.space_before_line_comments
                        else:
                            t.insertLeft(Tokens.SPACE, ' ' * self._options.space_before_line_comments)
                if self._options.check_space_before_line_comment_text:
                    # check for space after comment opening
                    comment_text = t.text
                    comment_witout_dash = comment_text.lstrip('-')
                    dash_count = len(comment_text) - len(comment_witout_dash)
                    comment_text = comment_witout_dash.lstrip()
                    comment_text = '-' * dash_count + self._options.space_before_line_comment_text * ' ' + comment_text
                    t.text = comment_text

        if self._options.check_space_before_line_comment or \
                self._options.check_space_before_line_comment_text:
            for t in tokens:
                do_check(t)

            # last comment is not included in edit(), because it only grab hidden token before the node
            last_tok = tokens.last().next([Tokens.SPACE, Tokens.NEWLINE, Tokens.SHEBANG, Tokens.COMMENT])
            if last_tok:
                do_check(last_tok)


    def apply(self, input):
        # try to get AST tree, do nothing if invalid source code is provided
        try:
            tree = ast.parse(input)
        except ast.SyntaxException as e:
            logging.error(str(e))
            return input

        # indent
        IndentVisitor(self._options).visit(tree)

        tokens = tree.edit()
        self.check_comma(tokens)
        self.check_line_comments(tokens)

        # simply return modified tokens to source
        return tree.edit().allToSource()
