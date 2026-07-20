import logging
from luaparser import ast, astnodes
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
    # Updated for luaparser >=4.0 / antlr4 LuaLexer token types
    # See: luaparser.parser.LuaLexer
    SEMCOL = 1        # was 55 (SEMI)
    EQ = 2            # was 31; also ASSIGN (antlr4: single = token)
    BREAK = 3         # was 2
    GOTO = 4          # was 10
    DO = 5            # was 3
    END = 6           # was 6
    WHILE = 7         # was 22
    REPEAT = 8        # was 17
    UNTIL = 9         # was 21
    IFTOK = 10        # was 11 (IF)
    THEN = 11         # was 19
    ELSEIF = 12       # was 5
    ELSETOK = 13      # was 4 (ELSE)
    FOR = 14          # was 8
    COMMA = 15        # was 51
    IN = 16           # was 12
    FUNCTION = 17     # was 9
    LOCAL = 18        # was 13
    LT = 19           # was 35
    GT = 20           # was 36
    RETURN = 21       # was 18
    COLCOL = 22       # was 49 (CC = ::)
    NIL = 23          # was 14
    FALSE = 24        # was 7
    TRUE = 25         # was 20
    DOT = 26          # was 54
    BITNOT = 27       # was 40 (SQUIG = ~)
    MINUS = 28        # was 24
    LENGTH = 29       # was 30 (POUND = #)
    OPAR = 30         # was 43 (OP = ()
    CPAR = 31         # was 44 (CP = ))
    NOT = 32          # was 15
    BITRLEFT = 33     # was 42 (LL = <<)
    BITRSHIFT = 34    # was 41 (GG = >>)
    BITAND = 35       # was 38 (AMP = &)
    FLOOR = 36        # was 27 (SS = //)
    MOD = 37          # was 28 (PER = %)
    COL = 38          # was 50
    LTEQ = 39         # was 33 (LE = <=)
    GTEQ = 40         # was 34 (GE = >=)
    AND = 41          # was 1
    OR = 42           # was 16
    ADD = 43          # was 23 (PLUS = +)
    MULT = 44         # was 25 (STAR = *)
    OBRACK = 45       # was 47 (OCU = [)
    CBRACK = 46       # was 48 (CCU = ])
    OBRACE = 47       # was 45 (OB = {)
    CBRACE = 48       # was 46 (CB = })
    NEQ = 49          # was 32 (EE = ~=)
    CONCAT = 50       # was 53 (DD = ..)
    BITOR = 51        # was 39 (PIPE = |)
    POW = 52          # was 29 (CARET = ^)
    DIV = 53          # was 26 (SLASH = /)
    VARARGS = 54      # was 52 (DDD = ...)
    NAME = 56         # was 56
    STRING = 57       # was 58 (NORMALSTRING)
    NORMALSTRING = 57
    CHARSTRING = 58
    LONGSTRING = 59
    NUMBER = 60       # was 57 (INT, most common)
    INT = 60
    HEX = 61
    FLOAT = 62
    HEX_FLOAT = 63
    COMMENT = 64      # was 59
    LINE_COMMENT = 65 # was 60
    SPACE = 66        # was 61 (WS)
    NEWLINE = 67      # was 62 (NL)
    SHEBANG = 68      # was 63
    ASSIGN = 2        # was 37, same as EQ (antlr4 single =)


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
    cdef CCommonToken _indentation_token

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
    cdef unordered_set[int] STRING_TYPES
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

    cdef bool next_rc(self, hidden_right=?)

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

    cdef inline int get_current_indent(self)
