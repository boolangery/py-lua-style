import logging
from luaparser import ast, astnodes
from luaparser.builder import Tokens
from enum import Enum
from antlr4.Token import CommonToken
# cython import
from libcpp cimport bool
from libcpp.vector cimport vector
import json


cdef class IndentOptions:
    def __init__(self):
        self.indent_size = 2

        self.indent_char = ' '
        self.indent_with_tabs = False
        self.initial_indent_level = 0
        self.close_on_lowest_level = False

        self.func_cont_line_level = 2
        self.break_if_statement = False
        self.break_for_statement = False
        self.break_while_statement = False

        self.space_around_op = False
        self.check_space_before_line_comment_text = False
        self.space_before_line_comment_text = 1
        self.space_around_assign = False
        self.check_param_list = False
        self.check_field_list = False
        self.skip_semi_colon = False
        self.if_cont_line_level = 0
        self.smart_table_align = False

        self.force_func_call_space_checking = False
        self.func_call_space_n = 0

    def to_json(self):
        """
            Convert this cython object to json.
            (no __dict__ attribute)
        """
        attributes = {
            'indent_size':                          self.indent_size,

            'indent_char':                          self.indent_char,
            'indent_with_tabs':                     self.indent_with_tabs,
            'initial_indent_level':                 self.initial_indent_level,
            'close_on_lowest_level':                self.close_on_lowest_level,

            'func_cont_line_level':                 self.func_cont_line_level,
            'break_if_statement':                   self.break_if_statement,
            'break_for_statement':                  self.break_for_statement,
            'break_while_statement':                self.break_while_statement,

            'space_around_op':                      self.space_around_op,
            'check_space_before_line_comment_text': self.check_space_before_line_comment_text,
            'space_before_line_comment_text':       self.space_before_line_comment_text,
            'space_around_assign':                  self.space_around_assign,
            'check_param_list':                     self.check_param_list ,
            'check_field_list':                     self.check_field_list,
            'skip_semi_colon':                      self.skip_semi_colon,
            'if_cont_line_level':                   self.if_cont_line_level,
            'smart_table_align':                    self.smart_table_align,

            'force_func_call_space_checking':       self.force_func_call_space_checking,
            'func_call_space_n':                    self.func_call_space_n,
        }
        return json.dumps(attributes,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '))

    @staticmethod
    def from_json(raw_json):
        """
            Convert from json to this cython object.
            (no __dict__ attribute)
        """
        attributes = json.loads(raw_json)
        options = IndentOptions()
        options.indent_size                         = attributes['indent_size']

        options.indent_char                         = attributes['indent_char']
        options.indent_with_tabs                    = attributes['indent_with_tabs']
        options.initial_indent_level                = attributes['initial_indent_level']
        options.close_on_lowest_level               = attributes['close_on_lowest_level']

        options.func_cont_line_level                = attributes['func_cont_line_level']
        options.break_if_statement                  = attributes['break_if_statement']
        options.break_for_statement                 = attributes['break_for_statement']
        options.break_while_statement               = attributes['break_while_statement']

        options.space_around_op                     = attributes['space_around_op']
        options.check_space_before_line_comment_text= attributes['check_space_before_line_comment_text']
        options.space_before_line_comment_text      = attributes['space_before_line_comment_text']
        options.space_around_assign                 = attributes['space_around_assign']
        options.check_param_list                    = attributes['check_param_list']
        options.check_field_list                    = attributes['check_field_list']
        options.skip_semi_colon                     = attributes['skip_semi_colon']
        options.if_cont_line_level                  = attributes['if_cont_line_level']
        options.smart_table_align                   = attributes['smart_table_align']

        options.force_func_call_space_checking      = attributes['force_func_call_space_checking']
        options.func_call_space_n                   = attributes['func_call_space_n']
        return options


cdef class IndentProcessor:
    HIDDEN_TOKEN_WITHOUT_COMMENTS = [
        CTokens.SHEBANG,
        CTokens.NEWLINE,
        CTokens.SPACE,
        -2]

    REL_OPERATORS = [
        CTokens.LT,
        CTokens.GT,
        CTokens.LTEQ,
        CTokens.GTEQ,
        CTokens.NEQ,
        CTokens.EQ]

    def __init__(self, options, stream):
        # constants init
        self.CLOSING_TOKEN.insert(CTokens.END)
        self.CLOSING_TOKEN.insert(CTokens.CBRACE)
        self.CLOSING_TOKEN.insert(CTokens.CPAR)

        self.HIDDEN_TOKEN.insert(CTokens.SHEBANG)
        self.HIDDEN_TOKEN.insert(CTokens.LINE_COMMENT)
        self.HIDDEN_TOKEN.insert(CTokens.COMMENT)
        self.HIDDEN_TOKEN.insert(CTokens.NEWLINE)
        self.HIDDEN_TOKEN.insert(CTokens.SPACE)
        self.HIDDEN_TOKEN.insert(-2)

        self._stream = stream
        # contains a list of CommonTokens
        self._src = []
        self._opt = options
        # current level
        self._level = 0
        self._line_count = 0
        self._right_index = 0
        self._last_expr_type = None

        # following stack are used to backup values
        self._index_stack = []
        self._src_index_stack = []
        self._level_stack = []
        self._right_index_stack = []
        self._last_tok_text_stack = []

        # append the first indentation token
        t = CommonToken()
        t.type = -2  # indentation type
        t.text = self._opt.indent_char * self.get_current_indent()
        self._src.append(t)

    cdef void inc_level(self, int n=1):
        self._level += n

    cdef void dec_level(self, int n=1):
        self._level -= n
        #logging.debug('<%s dec level, level=%d', self._debug_level * 2 * '*', self._level)

    cpdef process(self):
        if self._opt.indent_with_tabs:
            self._opt.indent_char = '\t'

        if not self.parse_chunk():
            raise Exception("Expecting a chunk")

        src = ''.join([t.text for t in self._src])
        return src

    cdef bool ws(self, int size):
        cdef object last
        cdef bool new_line

        last = self._src[-1]
        new_line = (len(self._src) > 1) and ((self._src[-2].type == CTokens.NEWLINE) or (self._src[-1].type == CTokens.NEWLINE))

        if not new_line:
            if last.type == CTokens.SPACE:
                last.text = ' ' * size
            else:
                t = CommonToken()
                t.type = CTokens.SPACE  # indentation token
                t.text = ' ' * size
                self.render(t)

        return True

    cdef bool ensure_newline(self):
        cdef object t

        # pop trailing space
        if self._src[-1].type == CTokens.SPACE:
            self._src.pop()

        for t in reversed(self._src):
            if t.type == CTokens.NEWLINE:
                return True
            elif not t.type in self.HIDDEN_TOKEN_WITHOUT_COMMENTS:
                break

        t = CommonToken()
        t.type = CTokens.NEWLINE
        t.text = '\n'
        self.render(t)

        return True

    cdef void save(self):
        #logging.debug('trying ' + inspect.stack()[1][3])
        self._index_stack.push_back(self._stream.index)
        self._src_index_stack.push_back(len(self._src))
        self._level_stack.push_back(self._level)
        self._right_index_stack.push_back(self._right_index)
        self._last_tok_text_stack.append(self._src[-1].text)

    cdef void render(self, object token):
        if self._src and self._src[-1].type == CTokens.NEWLINE:
            t = CommonToken()
            t.type = -2  # indentation token
            t.text = self._opt.indent_char * self.get_current_indent()
            self._src.append(t)
            self._line_count += 1

        elif not self._opt.close_on_lowest_level:
            if self.CLOSING_TOKEN.find(token.type) != self.CLOSING_TOKEN.end():
                for prev in reversed(self._src):
                    if self.CLOSING_TOKEN.find(prev.type) != self.CLOSING_TOKEN.end():
                        pass  # continue
                    elif prev.type == -2:
                        # set on current level
                        prev.text = self._opt.indent_char * self.get_current_indent()
                    else:
                        break

        self._src.append(token)
        #logging.debug('render %s <--------------', token)

    cdef bool success(self):
        self._index_stack.pop_back()
        self._src_index_stack.pop_back()
        self._level_stack.pop_back()
        self._right_index_stack.pop_back()
        self._last_tok_text_stack.pop()
        #logging.debug('success ' + inspect.stack()[1][3])
        return True

    cdef bool failure(self):
        cdef int n_elem_to_delete

        #logging.debug('failure ' + inspect.stack()[1][3])
        self._stream.seek(self._index_stack.back())
        self._index_stack.pop_back()

        n_elem_to_delete = len(self._src) - self._src_index_stack.back()
        self._src_index_stack.pop_back()
        if n_elem_to_delete >= 1:
            del self._src[-n_elem_to_delete:]
        self._level = self._level_stack.back()
        self._level_stack.pop_back()
        self._right_index = self._right_index_stack.back()
        self._right_index_stack.pop_back()
        self._src[-1].text = self._last_tok_text_stack.pop()
        return False

    cdef void failure_save(self):
        self.failure()
        self.save()

    cdef bool next_is_rc(self, int type, hidden_right=True):
        """rc is for render and consume token."""
        cdef object token
        cdef int toktype

        token = self._stream.LT(1)
        toktype = token.type
        self._right_index = self._stream.index

        if toktype == type:
            self._stream.consume()
            self.render(token)
            if hidden_right:
                self.handle_hidden_right()
            return True

        return False

    cdef bool next_is_c(self, int type, hidden_right=True):
        """c is for consume token."""
        cdef object token
        cdef int toktype

        token = self._stream.LT(1)
        toktype = token.type
        self._right_index = self._stream.index

        if toktype == type:
            self._stream.consume()
            if hidden_right:
                self.handle_hidden_right()
            return True

        return False

    cdef bool next_is(self, int type, int offset=0):
        return self._stream.LT(1 + offset).type == type

    cdef bool next_in_rc(self, unordered_set[int] types, bool hidden_right=True):
        cdef object token
        cdef int tok_type

        token = self._stream.LT(1)
        tok_type = token.type
        self._right_index = self._stream.index

        if types.find(tok_type) != types.end():
            self._stream.consume()
            self.render(token)
            if hidden_right:
                self.handle_hidden_right()

            return True

        return False

    cdef bool next_in_rc_cont(self, unordered_set[int] types, hidden_right=True):
        cdef bool is_newline
        cdef int space_count

        is_newline = False
        token = self._stream.LT(1)
        self._right_index = self._stream.index

        if types.find(token.type) != types.end():
            self._stream.consume()
            # pop hidden tokens
            hidden_stack = []

            for t in reversed(self._src):
                if t.type == CTokens.NEWLINE:
                    is_newline = True
                    hidden_stack.insert(0, self._src.pop())
                elif self.HIDDEN_TOKEN.find(t.type) != self.HIDDEN_TOKEN.end():
                    hidden_stack.insert(0, self._src.pop())
                else:
                    break

            self.render(token)
            self._src.extend(hidden_stack)

            if hidden_right:
                self.handle_hidden_right(is_newline)

            # merge last spaces
            space_count = 0
            for t in reversed(self._src):
                if t.type == CTokens.SPACE:
                    space_count += len(t.text)
                    tok = self._src.pop()
                else:
                    break
            if space_count > 0:
                tok.text = ' ' * space_count
                self._src.append(tok)

            return True

        return False

    cdef void strip_hidden(self):
        while self.HIDDEN_TOKEN.find(self._src[-1].type) != self.HIDDEN_TOKEN.end():
            self._src.pop()

    cdef int get_column_of_last(self):
        cdef int column
        cdef object t
        column = 0

        for t in reversed(self._src):
            if t.type == CTokens.NEWLINE:
                break
            else:
                column += len(t.text)
        return column

    cdef object get_previous_comment(self):
        cdef object t

        for t in reversed(self._src):
            if t.type == CTokens.LINE_COMMENT:
                return t
            elif self.HIDDEN_TOKEN.find(t.type) == self.HIDDEN_TOKEN.end():
                break
        return None

    cdef str get_previous_comment_str(self):
        cdef object t

        for t in reversed(self._src):
            if t.type == CTokens.LINE_COMMENT:
                return t.text.lstrip('- ')
            elif self.HIDDEN_TOKEN.find(t.type) == self.HIDDEN_TOKEN.end():
                break
        return ""

    cdef bool next_in(self, types):
        return self._stream.LT(1).type in types

    cdef void handle_hidden_left(self):
        is_newline = len(self._src) == 1  # empty token
        tokens = self._stream.getHiddenTokensToLeft(self._stream.index)
        if tokens:
            for t in tokens:
                if t.type == CTokens.NEWLINE:
                    self.render(t)
                    is_newline = True
                elif t.type == CTokens.SPACE:
                    if not is_newline:
                        self.render(t)
                else:
                    self.render(t)
                    is_newline = False

    cdef void handle_hidden_right(self, bool is_newline=False):
        cdef object t

        tokens = self._stream.getHiddenTokensToRight(self._right_index)
        if tokens:
            for t in tokens:
                # TODO: replace with a map
                if t.type == CTokens.NEWLINE:
                    self.render(t)
                    is_newline = True
                elif t.type == CTokens.SPACE:
                    if not is_newline:
                        if self._src:  # do not begin with a space
                            self.render(t)
                elif self._opt.check_space_before_line_comment_text and \
                        t.type == CTokens.LINE_COMMENT:
                    # check for space after comment opening
                    comment_text = t.text
                    comment_witout_dash = comment_text.lstrip('-')
                    dash_count = len(comment_text) - len(comment_witout_dash)
                    comment_text = comment_witout_dash.lstrip()
                    comment_text = '-' * dash_count + self._opt.space_before_line_comment_text * ' ' + comment_text
                    t.text = comment_text
                    self.render(t)
                    is_newline = False
                else:
                    self.render(t)
                    is_newline = False

    cdef bool parse_chunk(self):
        self._stream.LT(1)
        self.handle_hidden_left()
        if self.parse_block():
            token = self._stream.LT(1)
            if token.type == -1:
                # do not consume EOF
                return True
        return False

    cdef bool parse_block(self):
        while self.parse_stat():
            pass
        self.parse_ret_stat()
        return True

    cdef bool parse_stat(self):
        # check first most common statements
        if self.parse_assignment() \
                or self.parse_var(True) \
                or self.parse_do_block() \
                or self.parse_while_stat() \
                or self.parse_local() \
                or self.parse_if_stat() \
                or self.parse_for_stat() \
                or self.parse_function():
            # re-indent right hidden token after leaving the statement
            self.strip_hidden()
            self.handle_hidden_right()
            return True

        # handle the ambiguous syntax
        # http://lua-users.org/lists/lua-l/2009-08/msg00543.html
        # example:
        #   a = b + c;
        #   (print or io.write)('foo')
        elif self.next_is(CTokens.SEMCOL):
            ambiguous_syntax = False
            if not self._opt.skip_semi_colon:
                self.next_is_rc(CTokens.SEMCOL)
            else:
                if self.next_is(CTokens.OPAR, 1):
                    # ambiguous syntax detected, keep semi-colon
                    self.next_is_rc(CTokens.SEMCOL)
                    ambiguous_syntax = True
                else:
                    self.next_is_c(CTokens.SEMCOL)

            self.strip_hidden()
            self.handle_hidden_right()

            if ambiguous_syntax:
                # append a preventive comment
                comment = self.get_previous_comment()

                if comment is not None:
                    comment.text += ' / ambiguous syntax, previous semicolon is needed'
                else:
                    self.ws(1)
                    amb_comment = CommonToken()
                    amb_comment.type = CTokens.LINE_COMMENT
                    amb_comment.text = '-- ambiguous syntax, previous semicolon is needed'
                    self._src.append(amb_comment)
                    self.ensure_newline()

            return True

        elif (self.next_is(CTokens.BREAK) and self.next_is_rc(CTokens.BREAK)) \
                or self.parse_label() \
                or self.parse_repeat_stat() \
                or self.parse_goto_stat():
            # re-indent right hidden token after leaving the statement
            self.strip_hidden()
            self.handle_hidden_right()
            return True

        return False

    cdef bool parse_ret_stat(self):
        self.save()
        if self.next_is_rc(CTokens.RETURN):
            self.parse_expr_list()  # optional

            self.save()
            if (self._opt.skip_semi_colon and self.next_is_c(CTokens.SEMCOL)) or \
                    (not self._opt.skip_semi_colon and self.next_is_rc(CTokens.SEMCOL)):
                self.success()
            else:
                self.failure()

            return self.success()
        return self.failure()

    cdef bool parse_assignment(self):
        self.save()
        if self.parse_var_list():
            if (not self._opt.space_around_assign or self.ws(1)) and \
                    self.next_is_rc(CTokens.ASSIGN) and \
                    (not self._opt.space_around_assign or self.ws(1)):
                if self.parse_expr_list():
                    return self.success()
        return self.failure()

    cdef bool parse_var_list(self):
        self.save()
        if self.parse_var():
            while True:
                self.save()
                if (not self._opt.check_param_list or self.ws(0)) and \
                        self.next_is_rc(CTokens.COMMA) and \
                        (not self._opt.check_param_list or self.ws(1)) and \
                        self.parse_var():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        return self.failure()

    cdef bool parse_var(self, bool is_stat=False):
        cdef int number_of_chained_tail
        cdef int number_of_tail
        cdef int n
        cdef int line
        cdef int n_to_inc
        cdef bool on_several_lines
        cdef bool level_increased
        cdef ParseTailResult tail

        self.save()
        # first pass is used to count the number of tails and in case
        # of no need to re-indent (chained call for example), return directly
        on_several_lines = False
        level_increased = False
        number_of_chained_tail = 0
        number_of_tail = 0
        n_to_inc = -1

        if self.parse_callee():
            line = self._line_count
            while True:
                tail = self.parse_tail()
                if tail.success:
                    self.handle_hidden_right()
                    if tail.is_chainable:
                        number_of_chained_tail += 1
                    if not on_several_lines and (tail.last_line > line):
                        on_several_lines = True
                        n_to_inc = number_of_tail
                    number_of_tail += 1
                else:
                    break

            # if there are less than 2 tail or not in a statement return
            if number_of_tail < 2 or not is_stat:
                return self.success()


        if number_of_chained_tail > 1:
            n_to_inc = 0

        self.failure_save()
        if self.parse_callee():
            for n in range(0, number_of_tail-1):
                if not level_increased and on_several_lines and n_to_inc==n:
                    self.inc_level()
                    level_increased = True
                self.parse_tail()
                self.handle_hidden_right()

            if not level_increased and on_several_lines and n_to_inc==number_of_tail-1:
                self.inc_level()
                level_increased = True

            self.parse_tail()

            if level_increased:
                self.dec_level()

            self.handle_hidden_right()
            return self.success()

        return self.failure()

    cdef ParseTailResult parse_tail(self):
        cdef ParseTailResult result
        result.is_chainable = True
        result.success = True

        # do not render last hidden
        self.save()
        if self.next_is_rc(CTokens.DOT) and self.next_is_rc(CTokens.NAME, False):
            result.last_line = self._line_count
            self.success()
            return result

        self.failure_save()
        if self.next_is_rc(CTokens.OBRACK) and self.parse_expr() and self.next_is_rc(CTokens.CBRACK, False):
            result.last_line = self._line_count
            self.success()
            return result

        self.failure_save()
        if self.next_is_rc(CTokens.COL) and self.next_is_rc(CTokens.NAME):

            if self._opt.force_func_call_space_checking:
                self.ws(self._opt.func_call_space_n)

            result.last_line = self._line_count
            if self.next_is_rc(CTokens.OPAR, False):
                self.inc_level()
                self.handle_hidden_right()
                self.parse_expr_list(False, True) # force no indentation
                self.dec_level()
                if self.next_is_rc(CTokens.CPAR, False):
                    self.success()
                    return result

        self.failure_save()
        if self.next_is_rc(CTokens.COL) and self.next_is_rc(CTokens.NAME):
            result.last_line = self._line_count
            if self.parse_table_constructor(False):
                self.success()
                return result

        self.failure_save()
        if self.next_is_rc(CTokens.COL) and self.next_is_rc(CTokens.NAME):
            result.last_line = self._line_count
            if self.next_is_rc(CTokens.STRING, False):
                self.success()
                return result

        self.failure_save()

        if self._opt.force_func_call_space_checking:
            self.ws(self._opt.func_call_space_n)

        if self.next_is_rc(CTokens.OPAR, False):
            self.inc_level()
            self.handle_hidden_right()
            self.parse_expr_list(False, True)
            self.dec_level()
            if self.next_is_rc(CTokens.CPAR, False):
                result.is_chainable = False
                self.success()
                return result

        self.failure_save()
        if self.parse_table_constructor(False):
            result.is_chainable = False
            self.success()
            return result

        self.failure_save()
        if self.next_is_rc(CTokens.STRING, False):
            result.is_chainable = False
            self.success()
            return result

        result.success = False
        self.failure()
        return result

    cdef bool parse_expr_list(self, bool force_indent=False, bool force_no_indent=False):
        cdef bool several_expr
        self.save()

        # first pass to check if we need to indent
        # FIXME: find a better way to do this
        if not force_indent:
            several_expr = False
            if self.parse_expr():
                while True:
                    self.save()
                    if (not self._opt.check_param_list or self.ws(0)) and \
                            self.next_is_rc(CTokens.COMMA) and \
                            (not self._opt.check_param_list or self.ws(1)) and \
                            self.parse_expr():
                        several_expr = True
                        self.success()
                    else:
                        self.failure()
                        break

            if (not several_expr and self._last_expr_type == Expr.EXPR_ATOM) or force_no_indent:
                return self.success()  # just one expr and atom, no indent
        # restore and re-indent
        self.failure_save()
        self.inc_level()
        if self.parse_expr():
            while True:
                self.save()
                if (not self._opt.check_param_list or self.ws(0)) and \
                        self.next_is_rc(CTokens.COMMA) and \
                        (not self._opt.check_param_list or self.ws(1)) and \
                        self.parse_expr():
                    self.success()
                else:
                    self.failure()
                    break
            self.dec_level()
            return self.success()
        return self.failure()

    cdef bool parse_do_block(self, bool break_stat = False):
        self.save()
        if self.next_is_rc(CTokens.DO, False):
            self.inc_level()
            self.handle_hidden_right()
            if break_stat:
                self.ensure_newline()
            if self.parse_block():
                self.dec_level()
                if break_stat:
                    self.ensure_newline()
                if self.next_is_rc(CTokens.END):
                    return self.success()
        return self.failure()

    cdef bool parse_while_stat(self):
        self.save()
        if self.next_is_rc(CTokens.WHILE) and self.parse_expr() and self.parse_do_block(self._opt.break_while_statement):
            return self.success()

        return self.failure()

    cdef bool parse_repeat_stat(self):
        self.save()
        if self.next_is_rc(CTokens.REPEAT, False):
            self.inc_level()
            self.handle_hidden_right()
            if self._opt.break_while_statement:
                self.ensure_newline()
            if self.parse_block():
                self.dec_level()
                if self._opt.break_while_statement:
                    self.ensure_newline()
                if self.next_is_rc(CTokens.UNTIL) and self.parse_expr():
                    return self.success()

        return self.failure()

    cdef bool parse_local(self):
        self.save()
        if self.next_is_rc(CTokens.LOCAL):
            self.save()
            if self.parse_name_list():
                # optional
                self.save()
                if (not self._opt.space_around_assign or self.ws(1)) and \
                        self.next_is_rc(CTokens.ASSIGN) and \
                        (not self._opt.space_around_assign or self.ws(1)) and \
                        self.parse_expr_list():
                    self.success()
                else:
                    self.failure()
                self.success()
                return self.success()

            self.failure_save()
            if self.next_is_rc(CTokens.FUNCTION) and self.next_is_rc(CTokens.NAME) and self.parse_func_body():
                self.success()
                return self.success()
            self.failure()

        return self.failure()

    cdef bool parse_goto_stat(self):
        self.save()
        if self.next_is_rc(CTokens.GOTO) and self.next_is_rc(CTokens.NAME):
            return self.success()
        return self.failure()

    cdef bool parse_if_stat(self):
        self.save()
        if self.next_is_rc(CTokens.IFTOK):
            self.inc_level(self._opt.if_cont_line_level)
            if self.parse_expr():
                self.dec_level(self._opt.if_cont_line_level)
                if self.next_is_rc(CTokens.THEN, False):
                    self.inc_level()
                    self.handle_hidden_right()
                    if self._opt.break_if_statement:
                        self.ensure_newline()
                    if self.parse_block():
                        self.dec_level()
                        while self.parse_elseif_stat():  # one or more
                            pass
                        self.parse_else_stat()  # optional
                        if self._opt.break_if_statement:
                            self.ensure_newline()
                        if self.next_is_rc(CTokens.END):
                            return self.success()

        return self.failure()

    cdef bool parse_elseif_stat(self):
        self.save()
        if self.next_is(CTokens.ELSEIF):
            if self._opt.break_if_statement:
                self.ensure_newline()
            if self.next_is_rc(CTokens.ELSEIF):
                self.inc_level(self._opt.if_cont_line_level)
                if self.parse_expr():
                    self.dec_level(self._opt.if_cont_line_level)
                    if self.next_is_rc(CTokens.THEN, False):
                        self.inc_level()
                        self.handle_hidden_right()
                        if self._opt.break_if_statement:
                            self.ensure_newline()
                        if self.parse_block():
                            self.dec_level()
                            return self.success()

        return self.failure()

    cdef bool parse_else_stat(self):
        self.save()
        if self.next_is(CTokens.ELSETOK):
            if self._opt.break_if_statement:
                self.ensure_newline()
            if self.next_is_rc(CTokens.ELSETOK, False):
                self.inc_level()
                self.handle_hidden_right()
                if self._opt.break_if_statement:
                    self.ensure_newline()
                if self.parse_block():
                    self.dec_level()
                    return self.success()

        return self.failure()

    cdef bool parse_for_stat(self):
        self.save()

        if self.next_is_rc(CTokens.FOR):
            self.save()
            if self.next_is_rc(CTokens.NAME) and \
                    (not self._opt.space_around_assign or self.ws(1)) and \
                    self.next_is_rc(CTokens.ASSIGN) and \
                    (not self._opt.space_around_assign or self.ws(1)) and \
                    self.parse_expr() and \
                    self.next_is_rc(CTokens.COMMA) and \
                    self.ws(1) and self.parse_expr():
                self.save()
                if self.next_is_rc(CTokens.COMMA) and  self.ws(1) and self.parse_expr():
                    self.success()
                else:
                    self.failure()
                if self.parse_do_block(self._opt.break_for_statement):
                    self.success()
                    return self.success()

            self.failure_save()
            if self.parse_name_list() and \
                    self.next_is_rc(CTokens.IN) and \
                    self.parse_expr_list(True) and \
                    self.parse_do_block(self._opt.break_for_statement):
                self.success()
                return self.success()
            self.failure()

        return self.failure()

    cdef bool parse_function(self):
        self.save()
        if self.next_is_rc(CTokens.FUNCTION) and self.parse_names():
            self.save()
            if self.next_is_rc(CTokens.COL) and self.next_is_rc(CTokens.NAME):
                if self.parse_func_body():
                    self.success()
                    return self.success()

            self.failure_save()
            if self.parse_func_body():
                self.success()
                return self.success()
            self.failure()

        return self.failure()

    cdef bool parse_names(self):
        self.save()
        if self.next_is_rc(CTokens.NAME):
            while True:
                self.save()
                if self.next_is_rc(CTokens.DOT) and self.next_is_rc(CTokens.NAME):
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    cdef bool parse_func_body(self):
        self.save()
        if self.next_is_rc(CTokens.OPAR, False):  # do not render right hidden
            self.inc_level(self._opt.func_cont_line_level)
            self.handle_hidden_right()  # render hidden after new level
            if self.parse_param_list():
                self.dec_level(self._opt.func_cont_line_level)
                if self.next_is_rc(CTokens.CPAR, False):  # do not render right hidden
                    self.inc_level()
                    self.handle_hidden_right()  # render hidden after new level
                    if self.parse_block():
                        self.dec_level()
                        if self.next_is_rc(CTokens.END):
                            return self.success()
        return self.failure()

    cdef bool parse_param_list(self):
        self.save()
        if self.parse_name_list():
            self.save()
            if (not self._opt.check_param_list or self.ws(0)) and \
                    self.next_is_rc(CTokens.COMMA) and \
                    (not self._opt.check_param_list or self.ws(1)) and \
                    self.next_is_rc(CTokens.VARARGS):
                self.success()
            else:
                self.failure()
            return self.success()
        self.failure_save()

        if self.next_is_rc(CTokens.VARARGS):
            return self.success()

        return self.success()

    cdef bool parse_name_list(self):
        self.save()
        if self.next_is_rc(CTokens.NAME):
            while True:
                self.save()
                if (not self._opt.check_param_list or self.ws(0)) and \
                        self.next_is_rc(CTokens.COMMA) and \
                        (not self._opt.check_param_list or self.ws(1)) \
                        and self.next_is_rc(CTokens.NAME):
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        return self.failure()

    cdef bool parse_label(self):
        self.save()
        if self.next_is_rc(CTokens.COLCOL) and self.next_is_rc(CTokens.NAME) and self.next_is_rc(CTokens.COLCOL):
            return self.success()

        return self.failure()

    cdef bool parse_callee(self):
        self.save()
        if self.next_is_rc(CTokens.OPAR):
            self.inc_level()
            if self.parse_expr():
                self.dec_level()
                if self.next_is_rc(CTokens.CPAR):
                    return self.success()
        self.failure()
        self.save()
        if self.next_is_rc(CTokens.NAME):
            return self.success()
        return self.failure()

    cdef bool parse_expr(self):
        return self.parse_or_expr()

    cdef bool parse_or_expr(self):
        self.save()
        if self.parse_and_expr():
            while True:
                self.save()
                if (not self._opt.space_around_op or self.ws(1)) and \
                        self.next_is_rc(CTokens.OR) and \
                        (not self._opt.space_around_op or self.ws(1)) and \
                        self.parse_and_expr():
                    self._last_expr_type = Expr.EXPR_OR
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    cdef bool parse_and_expr(self):
        self.save()
        if self.parse_rel_expr():
            while True:
                self.save()
                if (not self._opt.space_around_op or self.ws(1)) and \
                        self.next_is_rc(CTokens.AND) and \
                        (not self._opt.space_around_op or self.ws(1)) \
                        and self.parse_rel_expr():
                    self._last_expr_type = Expr.EXPR_AND
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    cdef bool parse_rel_expr(self):
        self.save()
        if self.parse_concat_expr():
            self.save()
            if (not self._opt.space_around_op or self.ws(1)) and \
                    self.next_in_rc(self.REL_OPERATORS) and \
                    (not self._opt.space_around_op or self.ws(1)) and \
                    self.parse_concat_expr():
                self._last_expr_type = Expr.EXPR_REL
                self.success()
            else:
                self.failure()
            return self.success()
        self.failure()

    cdef bool parse_concat_expr(self):
        self.save()
        if self.parse_add_expr():
            while True:
                self.save()
                if (not self._opt.space_around_op or self.ws(1)) and \
                        self.next_is_rc(CTokens.CONCAT) and \
                        (not self._opt.space_around_op or
                         self.ws(1)) and self.parse_add_expr():
                    self._last_expr_type = Expr.EXPR_CONCAT
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    cdef bool parse_add_expr(self):
        self.save()
        if self.parse_mult_expr():
            while True:
                self.save()
                if (not self._opt.space_around_op or self.ws(1)) and \
                        self.next_in_rc([CTokens.ADD, CTokens.MINUS]) and \
                        (not self._opt.space_around_op or self.ws(1)) and \
                        self.parse_mult_expr():
                    self._last_expr_type = Expr.EXPR_ADD
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    cdef bool parse_mult_expr(self):
        self.save()
        if self.parse_bitwise_expr():
            while True:
                self.save()
                if (not self._opt.space_around_op or self.ws(1)) and self.next_in_rc([CTokens.MULT,
                                   CTokens.DIV,
                                   CTokens.MOD,
                                   CTokens.FLOOR]) and (not self._opt.space_around_op or self.ws(1)) and self.parse_bitwise_expr():
                    self._last_expr_type = Expr.EXPR_MULT
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    cdef bool parse_bitwise_expr(self):
        self.save()
        if self.parse_unary_expr():
            while True:
                self.save()
                if self.next_in_rc([CTokens.BITAND,
                                 CTokens.BITOR,
                                 CTokens.BITNOT,
                                 CTokens.BITRSHIFT,
                                 CTokens.BITRLEFT]) and self.parse_unary_expr():
                    self._last_expr_type = Expr.EXPR_BITWISE
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    cdef bool parse_unary_expr(self):
        self.save()
        if self.next_is_rc(CTokens.MINUS) and self.parse_unary_expr():
            self._last_expr_type = Expr.EXPR_UNARY
            return self.success()

        self.failure_save()
        if self.next_is_rc(CTokens.LENGTH) and self.parse_pow_expr():
            self._last_expr_type = Expr.EXPR_UNARY
            return self.success()

        self.failure_save()
        if self.next_is_rc(CTokens.NOT) and self.parse_unary_expr():
            self._last_expr_type = Expr.EXPR_UNARY
            return self.success()

        self.failure_save()
        if self.next_is_rc(CTokens.BITNOT) and self.parse_unary_expr():
            self._last_expr_type = Expr.EXPR_UNARY
            return self.success()

        self.failure_save()
        if self.parse_pow_expr():
            return self.success()

        return self.failure()

    cdef bool parse_pow_expr(self):
        self.save()
        if self.parse_atom():
            while True:
                self.save()
                if self.next_is_rc(CTokens.POW) and self.parse_atom():
                    self._last_expr_type = Expr.EXPR_POW
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    cdef bool parse_atom(self):
        self.save()
        if self.parse_var() or \
                self.parse_function_literal() or \
                self.parse_table_constructor() or \
                self.next_in_rc([CTokens.VARARGS,
                                 CTokens.NUMBER,
                                 CTokens.STRING,
                                 CTokens.NIL,
                                 CTokens.TRUE,
                                 CTokens.FALSE]):
            self._last_expr_type = Expr.EXPR_ATOM
            return self.success()
        return self.failure()

    cdef bool parse_function_literal(self):
        self.save()
        if self.next_is_rc(CTokens.FUNCTION) and self.parse_func_body():
            return self.success()

        return self.failure()

    cdef bool parse_table_constructor(self, render_last_hidden=True):
        cdef bool check_field_list
        check_field_list = self._opt.check_field_list

        self.save()
        if self.next_is_rc(CTokens.OBRACE, False):  # do not render right hidden
            self.inc_level()
            self.handle_hidden_right()  # render hidden after new level

            if check_field_list and (self.get_previous_comment_str() == "@luastyle.disable"):
                check_field_list = False

            self.parse_field_list(check_field_list)
            self.dec_level()
            if self.next_is_rc(CTokens.CBRACE, render_last_hidden):
                return self.success()
        return self.failure()

    cdef bool parse_field_list(self, bool check_field_list):
        cdef int k
        cdef int max_position
        cdef ParseFieldResult field_result
        cdef vector[ParseFieldResult] field_results
        cdef bool align_table

        if not self._opt.smart_table_align:
            self.save()
            if self.parse_field().success:
                while True:
                    self.save()
                    # if check_field_list, no space is allowed between COMMA and key
                    if self.next_in([CTokens.COMMA, CTokens.SEMCOL]) and \
                            ((check_field_list and self.next_in_rc_cont([CTokens.COMMA, CTokens.SEMCOL])) or \
                            (not check_field_list and self.next_in_rc([CTokens.COMMA, CTokens.SEMCOL]))) and \
                            (not check_field_list or self.ws(1)) and \
                            self.parse_field().success:
                        self.success()
                    else:
                        self.failure()
                        break
                self.parse_field_sep()
                return self.success()
            return self.failure()
        else:
            self.save()
            # first pass is used to count field and grab the postion
            # of the most left '='
            max_position = 0
            while True:
                field_result = self.parse_field()
                if field_result.success:
                    field_results.push_back(field_result)

                    # get '=' max position
                    if field_result.has_assign:
                        if field_result.assign_position > max_position:
                            max_position = field_result.assign_position

                    if not (self.next_in([CTokens.COMMA, CTokens.SEMCOL]) and self.next_in_rc([CTokens.COMMA, CTokens.SEMCOL])):
                        break
                else:
                    break

            if field_results.size() == 0:
                return self.failure()

            # condition to enable smart indent
            align_table = (field_results.size() > 3) and (max_position < 35)

            # pass to smart indent with previous results
            self.failure_save()
            k = 0
            for field_result in field_results:
                if field_result.has_assign and align_table:
                    self.parse_field(max_position - field_result.assign_position + 1)
                else:
                    self.parse_field()

                if k < field_results.size():
                    if self.next_in([CTokens.COMMA, CTokens.SEMCOL]) and \
                            ((check_field_list and self.next_in_rc_cont([CTokens.COMMA, CTokens.SEMCOL])) or \
                            (not check_field_list and self.next_in_rc([CTokens.COMMA, CTokens.SEMCOL]))) and \
                            (not check_field_list or self.ws(1)):
                        pass

                k += 1

            return self.success()


    cdef ParseFieldResult parse_field(self, int n_space_before_assign=-1):
        cdef ParseFieldResult result
        cdef bool space_before_assign
        space_before_assign = (n_space_before_assign >= 0)
        result.has_assign = False

        self.save()
        if self.next_is_rc(CTokens.OBRACK) and self.parse_expr() \
                and self.next_is_rc(CTokens.CBRACK):
            result.assign_position = self.get_column_of_last()

            if space_before_assign:
                self.ws(n_space_before_assign)

            if self.next_is_rc(CTokens.ASSIGN):
                result.has_assign = True

                if self.parse_expr():
                    result.success = self.success()
                    return result

        self.failure_save()
        if self.next_is_rc(CTokens.NAME):
            result.assign_position = self.get_column_of_last()

            if space_before_assign:
                self.ws(n_space_before_assign)

            if self.next_is_rc(CTokens.ASSIGN):
                result.has_assign = True

                if self.parse_expr():
                    result.success = self.success()
                    return result

        self.failure_save()
        if self.parse_expr():
            result.success = self.success()
            return result

        result.success = self.failure()
        return result

    cdef bool parse_field_sep(self):
        self.save()
        if self.next_in_rc([CTokens.COMMA, CTokens.SEMCOL]):
            return self.success()
        return self.failure()

    cdef int get_current_indent(self, int offset=0):
        if not self._opt.indent_with_tabs:
            return (self._level + offset + self._opt.initial_indent_level) * self._opt.indent_size
        else:
            return self._level + offset + self._opt.initial_indent_level


class IndentRule:
    """
    This rule indent the code.
    """
    def __init__(self, options):
        self._opt = options

    def apply(self, input):
        # tokenize source code
        stream = ast.get_token_stream(input)

        # indent
        processor = IndentProcessor(self._opt, stream)

        return processor.process()