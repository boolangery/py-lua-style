import logging
from luaparser import ast, astnodes
from luaparser.builder import Tokens
from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.unordered_set cimport unordered_set
from libcpp.string cimport string
import json


cdef class IndentOptions:
    """Define indentation options"""
    cdef public int indent_size
    cdef public char indent_char
    cdef public bool indent_with_tabs
    cdef public int initial_indent_level
    # in case of several closing token on the same line ('}', ')', 'end')
    # indent all line of last element level
    cdef public bool close_on_lowest_level

    # continuation lines
    cdef public int func_cont_line_level
    cdef public bool break_if_statement
    # break multiple statement on the same line
    cdef public bool break_for_statement
    cdef public bool break_while_statement

    # space checking
    cdef public bool space_around_op
    cdef public bool check_space_before_line_comment_text
    cdef public int space_before_line_comment_text

    # Ensure padding spaces around assignment operator '='
    cdef public bool space_around_assign
    # Ensure padding space after a comma in a param list
    cdef public bool check_param_list
    # Ensure padding space after a comma in a field list (table)
    cdef public bool check_field_list
    # Skip semi-colon at the end of all statements
    cdef public bool skip_semi_colon
    # Indentation level of if/elseif continuation lines
    cdef public int if_cont_line_level
    cdef public bool smart_table_align

    # function checking
    # Ensure x space after a function call
    cdef public bool force_func_call_space_checking
    cdef public int func_call_space_n


cdef enum Expr:
    EXPR_OR      = 1
    EXPR_AND     = 2
    EXPR_REL     = 3
    EXPR_CONCAT  = 4
    EXPR_ADD     = 5
    EXPR_MULT    = 6
    EXPR_BITWISE = 7
    EXPR_UNARY   = 8
    EXPR_POW     = 9
    EXPR_ATOM    = 10


cdef enum CTokens:
    AND = 1
    BREAK = 2
    DO = 3
    ELSETOK = 4
    ELSEIF = 5
    END = 6
    FALSE = 7
    FOR = 8
    FUNCTION = 9
    GOTO = 10
    IFTOK = 11
    IN = 12
    LOCAL = 13
    NIL = 14
    NOT = 15
    OR = 16
    REPEAT = 17
    RETURN = 18
    THEN = 19
    TRUE = 20
    UNTIL = 21
    WHILE = 22
    ADD = 23
    MINUS = 24
    MULT = 25
    DIV = 26
    FLOOR = 27
    MOD = 28
    POW = 29
    LENGTH = 30
    EQ = 31
    NEQ = 32
    LTEQ = 33
    GTEQ = 34
    LT = 35
    GT = 36
    ASSIGN = 37
    BITAND = 38
    BITOR = 39
    BITNOT = 40
    BITRSHIFT = 41
    BITRLEFT = 42
    OPAR = 43
    CPAR = 44
    OBRACE = 45
    CBRACE = 46
    OBRACK = 47
    CBRACK = 48
    COLCOL = 49
    COL = 50
    COMMA = 51
    VARARGS = 52
    CONCAT = 53
    DOT = 54
    SEMCOL = 55
    NAME = 56
    NUMBER = 57
    STRING = 58
    COMMENT = 59
    LINE_COMMENT = 60
    SPACE = 61
    NEWLINE = 62
    SHEBANG = 63
    LongBracket = 64


cdef struct ParseFieldResult:
    bool success
    bool has_assign
    int assign_position


cdef struct ParseTailResult:
    bool success
    bool is_chainable
    int last_line


cdef struct CCommonToken:
    int type
    string text


cdef class IndentProcessor:
    cdef object _stream

    cdef vector[CCommonToken] _src
    cdef IndentOptions _opt

    cdef int _level
    cdef int _line_count
    cdef int _right_index
    cdef object _last_expr_type
    cdef bool _is_tail_chainable
    cdef int _tail_last_line

    cdef vector[int] _index_stack
    cdef vector[int] _src_index_stack
    cdef vector[int] _level_stack
    cdef vector[int] _right_index_stack
    cdef vector[bool] _is_tail_chainable_stack
    cdef vector[int] _tail_last_line_stack
    cdef vector[string] _last_tok_text_stack

    cdef unordered_set[int] CLOSING_TOKEN
    cdef unordered_set[int] HIDDEN_TOKEN
    cdef unordered_set[int] HIDDEN_TOKEN_WITHOUT_COMMENTS
    cdef unordered_set[int] REL_OPERATORS
    cdef unordered_set[int] ADD_MINUS_OP
    cdef unordered_set[int] MULT_OP
    cdef unordered_set[int] BITWISE_OP
    cdef unordered_set[int] ATOM_OP
    cdef unordered_set[int] COMMA_SEMCOL

    cdef inline void inc_level(self, int n=1)

    cdef inline void dec_level(self, int n=1)

    cpdef str process(self)

    cdef bool ws(self, int size)

    cdef bool ensure_newline(self)

    cdef inline void save(self)

    cdef void render(self, CCommonToken& token)

    cdef inline bool success(self)

    cdef inline bool failure(self)

    cdef inline void failure_save(self)

    cdef bool next_is_rc(self, int type, hidden_right=?)

    cdef bool next_is_c(self, int type, hidden_right=?)

    cdef bool next_is(self, int type, int offset=?)

    cdef bool next_in_rc(self, unordered_set[int]& types, bool hidden_right=?)

    cdef bool next_in_rc_cont(self, unordered_set[int]& types, bool hidden_right=?)

    cdef void strip_hidden(self)

    cdef int get_column_of_last(self)

    cdef CCommonToken* get_previous_comment(self)

    cdef str get_previous_comment_str(self)

    cdef inline bool next_in(self, unordered_set[int]& types)

    cdef void handle_hidden_left(self)

    cdef void handle_hidden_right(self, bool is_newline=?)

    cdef bool parse_chunk(self)

    cdef bool parse_block(self)

    cdef bool parse_stat(self)

    cdef bool parse_ret_stat(self)

    cdef bool parse_assignment(self)

    cdef bool parse_var_list(self)

    cdef bool parse_var(self, bool is_stat=?)

    cdef ParseTailResult parse_tail(self)

    cdef bool parse_expr_list(self, bool force_indent=?, bool force_no_indent=?)

    cdef bool parse_do_block(self, bool break_stat=?)

    cdef bool parse_while_stat(self)

    cdef bool parse_repeat_stat(self)

    cdef bool parse_local(self)

    cdef bool parse_goto_stat(self)

    cdef bool parse_if_stat(self)

    cdef bool parse_elseif_stat(self)

    cdef bool parse_else_stat(self)

    cdef bool parse_for_stat(self)

    cdef bool parse_function(self)

    cdef bool parse_names(self)

    cdef bool parse_func_body(self)

    cdef bool parse_param_list(self)

    cdef bool parse_name_list(self)

    cdef bool parse_label(self)

    cdef bool parse_callee(self)

    cdef bool parse_expr(self)

    cdef bool parse_or_expr(self)

    cdef bool parse_and_expr(self)

    cdef bool parse_rel_expr(self)

    cdef bool parse_concat_expr(self)

    cdef bool parse_add_expr(self)

    cdef bool parse_mult_expr(self)

    cdef bool parse_bitwise_expr(self)

    cdef bool parse_unary_expr(self)

    cdef bool parse_pow_expr(self)

    cdef bool parse_atom(self)

    cdef bool parse_function_literal(self)

    cdef bool parse_table_constructor(self, render_last_hidden=?)

    cdef bool parse_field_list(self, bool check_field_list)

    cdef ParseFieldResult parse_field(self, int n_space_before_assign=?)

    cdef bool parse_field_sep(self)

    cdef int get_current_indent(self, int offset=?)
