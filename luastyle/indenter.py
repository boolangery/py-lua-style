import logging
from luaparser import ast, astnodes, asttokens
from luaparser.asttokens import Tokens
from enum import Enum
from antlr4.Token import CommonToken
import inspect

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


class IndentProcessor:
    def __init__(self, options, stream):
        self._stream = stream
        self._src = []
        self._line = []
        self._options = options
        self._level = 0
        self._line_count = 0
        self._debug_level = 0

        # _modes is a stack of Modes, the last mode in the stack is
        # the current mode
        self._modes = []

        # _modes_model is Modes model stack
        self._modes_model = []

        # _flags is a dictionary of Flags associated to a boolean.
        self._flags = {}

        self._last_mode_left = None
        # map of line number associated to level
        self._level_line_map = {}
        self._index = -1
        self._line_close_multiple_levels = False

        self._index_stack = []
        self._src_index_stack = []
        self._right_index = 0

    def enter_mode(self, mode):
        logging.debug('%s> Enter %s', self._debug_level*2*'-', mode)
        self._debug_level += 1

        # create model
        if mode in CUSTOM_MODELS:
            model = CUSTOM_MODELS[mode]()
        else:
            model = BaseModel()

        # populate model
        model.line = self._line_count

        # push on stack
        current_mode = None
        if self._modes:
            current_mode = self._modes[-1]
        self._modes.append(mode)
        self._modes_model.append(model)

        # trigger events
        if mode in self._on_enter:
            self._on_enter[mode](model, current_mode)

        return model

    def leave_mode(self):
        # pop model
        model = self._modes_model.pop()
        mode = self._modes.pop()
        self._last_mode_left = mode

        self._debug_level -= 1
        logging.debug('<%s Leave %s', self._debug_level*2*'-', mode)

        # trigger events
        if mode in self._on_leave:
            self._on_leave[mode](model)

        return model

    def assert_leave_mode(self, mode):
        if self._modes[-1] == mode:
            self.leave_mode()
        else:
            raise Exception("Expected to leave mode " + str(mode))

    def in_mode(self, mode):
        return self._modes and (self._modes[-1] == mode)

    def in_modes(self, modes):
        return self._modes and (self._modes[-1] in modes)

    def get_mode_model(self):
        return self._modes_model[-1]

    def inc_level(self, n=1):
        self._level += n
        logging.debug('%s> inc level, level=%d', self._debug_level*2*'+', self._level)

    def dec_level(self, n=1):
        self._level -= n
        logging.debug('<%s dec level, level=%d', self._debug_level * 2 * '*', self._level)

    def process(self):
        src = []

        if not self.parse_chunk():
            raise Exception("Expecting a chunk")

        src = ''.join([t.text for t in self._src])
        return src

    def save(self):
        self._index_stack.append(self._stream.index)
        self._src_index_stack.append(len(self._src))

    def render(self, token):
        self._src.append(token)

    def success(self):
        self._index_stack.pop()
        self._src_index_stack.pop()
        #logging.debug('success ' + inspect.stack()[1][3])
        return True

    def failure(self):
        self._stream.seek(self._index_stack.pop())
        n_elem_to_delete = len(self._src) - self._src_index_stack.pop()
        if n_elem_to_delete > 1:
            del self._src[-n_elem_to_delete:]
        return False

    def failure_save(self):
        self._stream.seek(self._index_stack.pop())
        n_elem_to_delete = len(self._src) - self._src_index_stack.pop()
        if n_elem_to_delete > 1:
            del self._src[-n_elem_to_delete:]
        self._index_stack.append(self._stream.index)
        self._src_index_stack.append(len(self._src))

    def next_is(self, type):
        token = self._stream.LT(1)
        self._right_index = self._stream.index
        if token.type != -1:  # cannot consume eof
            self._stream.consume()
        if token.type == type.value:
            self.render(token)
            return True
        return False

    def next_in(self, types):
        token = self._stream.LT(1)
        if token.type != -1:  # cannot consume eof
            self._stream.consume()
        if token.type in [t.value for t in types]:
            self.render(token)
            return True
        return False

    def handle_hidden_left(self):
        tokens = self._stream.getHiddenTokensToLeft(self._stream.index)
        if tokens:
            for t in tokens:
                self._src.append(t)

    def handle_hidden_right(self):
        tokens = self._stream.getHiddenTokensToRight(self._right_index)
        if tokens:
            for t in tokens:
                self._src.append(t)

    def parse_chunk(self):
        self.save()
        if self.parse_block():
            token = self._stream.LT(1)
            if token.type == -1:
                # do not consume EOF
                return self.success()
        return self.failure()

    def parse_block(self):
        self.save()
        while self.parse_stat():
            pass
        self.parse_ret_stat()
        return self.success()

    def parse_stat(self):
        self.save()
        if self.parse_assignment() \
                or self.parse_var() \
                or self.parse_do_block() \
                or self.parse_while_stat() \
                or self.parse_repeat_stat() \
                or self.parse_local() \
                or self.parse_goto_stat() \
                or self.parse_if_stat() \
                or self.parse_for_stat() \
                or self.parse_function() \
                or self.parse_label() \
                or self.next_in([Tokens.BREAK, Tokens.SEMCOL]):
            return self.success()
        return self.failure()

    def parse_ret_stat(self):
        return False

    def parse_assignment(self):
        self.save()
        if self.parse_var_list():
            if self.next_is(Tokens.ASSIGN):
                if self.parse_expr_list():
                    return self.success()
        return self.failure()

    def parse_var_list(self):
        self.save()
        if self.parse_var():
            while True:
                self.save()
                if self.next_is(Tokens.COMMA) and self.parse_var():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        return self.failure()

    def parse_var(self):
        self.save()
        if self.parse_callee():
            while self.parse_tail():
                pass
            return self.success()
        return self.failure()

    def parse_tail(self):
        self.save()
        if self.next_is(Tokens.DOT) and self.next_is(Tokens.NAME):
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.OBRACK) and self.parse_expr() and self.next_is(Tokens.CBRACK):
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.COL) and self.next_is(Tokens.NAME) and self.next_is(Tokens.OPAR):
            self.parse_expr_list()
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.COL) and self.next_is(Tokens.NAME) and self.parse_table_constructor():
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.COL) and self.next_is(Tokens.NAME) and self.next_is(Tokens.STRING):
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.OPAR):
            self.parse_expr_list()
            if self.next_is(Tokens.CPAR):
                return self.success()

        self.failure_save()
        if self.parse_table_constructor():
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.STRING):
            return self.success()

        return self.failure()

    def parse_expr_list(self):
        self.save()
        if self.parse_expr():
            while True:
                self.save()
                if self.next_is(Tokens.COMMA) and self.parse_expr():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        return self.failure()

    def parse_do_block(self):
        self.save()
        if self.next_is(Tokens.DO):
            self.handle_hidden_right()
            if self.parse_block():
                if self.next_is(Tokens.END):
                    return self.success()
        return self.failure()

    def parse_while_stat(self):
        return False

    def parse_repeat_stat(self):
        return False

    def parse_local(self):
        return False

    def parse_goto_stat(self):
        return False

    def parse_if_stat(self):
        return False

    def parse_for_stat(self):
        return False

    def parse_function(self):
        self.save()
        if self.next_is(Tokens.FUNCTION) and self.parse_names():
            self.save()
            if self.next_is(Tokens.COL) and self.next_is(Tokens.NAME):
                if self.parse_func_body():
                    self.success()
                    return self.success()

            self.failure_save()
            if self.parse_func_body():
                return self.success()
            self.failure()

        return self.failure()

    def parse_names(self):
        self.save()
        if self.next_is(Tokens.NAME):
            while True:
                self.save()
                if self.next_is(Tokens.DOT) and self.next_is(Tokens.NAME):
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    def parse_func_body(self):
        self.save()
        if self.next_is(Tokens.OPAR):
            if self.parse_param_list():
                if self.next_is(Tokens.CPAR):
                    if self.parse_block():
                        if self.next_is(Tokens.END):
                            return self.success()
        return self.failure()

    def parse_param_list(self):
        self.save()
        if self.parse_name_list():
            self.save()
            if self.next_is(Tokens.COMMA) and self.next_is(Tokens.VARARGS):
                self.success()
            else:
                self.failure()
            return self.success()
        self.failure_save()

        if self.next_is(Tokens.VARARGS):
            return self.success()

        self.failure_save()
        return self.success()

        return self.failure()

    def parse_name_list(self):
        self.save()
        if self.next_is(Tokens.NAME):
            while True:
                self.save()
                if self.next_is(Tokens.COMMA) and self.next_is(Tokens.NAME):
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        return self.failure()

    def parse_label(self):
        return False

    def parse_callee(self):
        self.save()
        if self.next_is(Tokens.OPAR):
            if self.parse_expr():
                if self.next_is(Tokens.CPAR):
                    return self.success()
        self.failure()
        self.save()
        if self.next_is(Tokens.NAME):
            return self.success()
        return self.failure()

    def parse_expr(self):
        return self.parse_or_expr()

    def parse_or_expr(self):
        self.save()
        if self.parse_and_expr():
            while True:
                self.save()
                if self.next_is(Tokens.OR) and self.parse_and_expr():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    def parse_and_expr(self):
        self.save()
        if self.parse_rel_expr():
            while True:
                self.save()
                if self.next_is(Tokens.AND) and self.parse_rel_expr():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    def parse_rel_expr(self):
        self.save()
        if self.parse_concat_expr():
            self.save()
            if self.next_in([Tokens.LT,
                             Tokens.GT,
                             Tokens.LTEQ,
                             Tokens.GTEQ,
                             Tokens.NEQ,
                             Tokens.EQ]) and self.parse_concat_expr():
                self.success()
            else:
                self.failure()
            return self.success()
        self.failure()

    def parse_concat_expr(self):
        self.save()
        if self.parse_add_expr():
            while True:
                self.save()
                if self.next_is(Tokens.CONCAT) and self.parse_add_expr():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    def parse_add_expr(self):
        self.save()
        if self.parse_mult_expr():
            while True:
                self.save()
                if self.next_in([Tokens.ADD,
                                 Tokens.MINUS]) and self.parse_mult_expr():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    def parse_mult_expr(self):
        self.save()
        if self.parse_bitwise_expr():
            while True:
                self.save()
                if self.next_in([Tokens.MULT,
                                 Tokens.DIV,
                                 Tokens.MOD,
                                 Tokens.FLOOR]) and self.parse_bitwise_expr():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    def parse_bitwise_expr(self):
        self.save()
        if self.parse_unary_expr():
            while True:
                self.save()
                if self.next_in([Tokens.BITAND,
                                 Tokens.BITOR,
                                 Tokens.BITNOT,
                                 Tokens.BITRSHIFT,
                                 Tokens.BITRLEFT]) and self.parse_unary_expr():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    def parse_unary_expr(self):
        self.save()
        if self.next_is(Tokens.MINUS) and self.parse_unary_expr():
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.LENGTH) and self.parse_pow_expr():
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.NOT) and self.parse_unary_expr():
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.BITNOT) and self.parse_unary_expr():
            return self.success()

        self.failure_save()
        if self.parse_pow_expr():
            return self.success()

        return self.failure()

    def parse_pow_expr(self):
        self.save()
        if self.parse_atom():
            while True:
                self.save()
                if self.next_is(Tokens.POW) and self.parse_atom():
                    self.success()
                else:
                    self.failure()
                    break
            return self.success()
        self.failure()

    def parse_atom(self):
        self.save()
        if self.parse_var() or \
                self.parse_function_literal() or \
                self.parse_table_constructor() or \
                self.next_in([Tokens.VARARGS,
                              Tokens.NUMBER,
                              Tokens.STRING,
                              Tokens.NIL,
                              Tokens.TRUE,
                              Tokens.FALSE]):
            return self.success()
        return self.failure()

    def parse_function_literal(self):
        return False

    def parse_table_constructor(self):
        self.save()
        if self.next_is(Tokens.OBRACE):
            self.parse_field_list()
            if self.next_is(Tokens.CBRACE):
                return self.success()
        return self.failure()

    def parse_field_list(self):
        self.save()
        if self.parse_field():
            while True:
                self.save()
                if self.parse_field_sep() and self.parse_field():
                    self.success()
                else:
                    self.failure()
                    break
            self.parse_field_sep()
            return self.success()
        return self.failure()

    def parse_field(self):
        self.save()
        if self.next_is(Tokens.OBRACK) and self.parse_expr() \
                and self.next_is(Tokens.CBRACK) \
                and self.next_is(Tokens.ASSIGN) and self.parse_expr():
            return self.success()

        self.failure_save()
        if self.next_is(Tokens.NAME) and self.next_is(Tokens.ASSIGN) and self.parse_expr():
            return self.success()

        self.failure_save()
        if self.parse_expr():
            return self.success()

        return self.failure()

    def parse_field_sep(self):
        self.save()
        if self.next_in([Tokens.COMMA, Tokens.SEMCOL]):
            return self.success()
        return self.failure()

    def get_current_indent(self, offset=0):
        if not self._options.indent_with_tabs:
            return (self._level + offset + self._options.initial_indent_level) * self._options.indent_size
        else:
            return self._level + offset + self._options.initial_indent_level


class IndentRule(FormatterRule):
    """
    This rule indent the code.
    """
    def __init__(self, options):
        FormatterRule.__init__(self)
        self._options = options

    def apply(self, input):
        # tokenize source code
        stream = asttokens.get_token_stream(input)

        # indent
        processor = IndentProcessor(self._options, stream)

        return processor.process()
