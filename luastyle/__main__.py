#!/usr/bin/env python3
import sys
import os
import logging
from optparse import OptionParser, OptionGroup
import luastyle
from luastyle.core import FilesProcessor, Configuration
from luastyle.indenter import IndentOptions


def abort(msg):
    sys.stderr.write(msg + '\n')
    sys.exit()


def main():
    # parse options:
    parser = OptionParser(usage='usage: %prog [options] file|directory',
                          version='%prog ' + luastyle.__version__)
    cli_group = OptionGroup(parser, "CLI Options")
    cli_group.add_option('-i', '--in-place',
                         action='store_true',
                         dest='replace',
                         help='write output in-place, replacing input',
                         default=False)
    cli_group.add_option('--config',
                         metavar='F', type='string',
                         dest='config_file',
                         help='path to config file')
    cli_group.add_option('--config-generate',
                         action='store_true',
                         dest='config_generate',
                         help='generate a default config file',
                         default=False)
    cli_group.add_option('--type',
                         action="append",
                         type='string',
                         dest='extensions',
                         metavar='EXT',
                         help='file extension to indent (can be repeated) [lua]',
                         default=['lua'])
    cli_group.add_option('-d', '--debug',
                         action='store_true',
                         dest='debug',
                         help='enable debugging messages',
                         default=False)
    cli_group.add_option('-j', '--jobs',
                         metavar='N', type="int",
                         dest='jobs',
                         help='number of parallel jobs in recursive mode',
                         default=4)
    parser.add_option_group(cli_group)

    # Style options:
    default = IndentOptions()
    style_group = OptionGroup(parser, "Beautifier Options")
    style_group.add_option('-a', '--space-around-assign',
                           action='store_true',
                           dest='space_around_assign',
                           help='ensure one space before and after assign op "="',
                           default=False)
    style_group.add_option('-c', '--indent-char',
                           metavar='S', type='string',
                           dest='indent_char',
                           help='indentation character [" "]',
                           default=' ')
    style_group.add_option('-f', '--check-field-list',
                           action='store_true',
                           dest='check_field_list',
                           help='format field-list (table)',
                           default=False)
    style_group.add_option('-l', '--indent-level',
                           metavar='N', type='int',
                           dest='initial_indent_level',
                           help='initial indentation level [0]',
                           default=0)
    style_group.add_option('-p', '--check-param-list',
                           action='store_true',
                           dest='check_param_list',
                           help='format var-list, name-list and expr-list',
                           default=False)
    style_group.add_option('-s', '--indent-size',
                           metavar='N', type='int',
                           dest='indent_size',
                           help='indentation size [2]',
                           default=2)
    style_group.add_option('-t', '--indent-with-tabs',
                           action='store_true',
                           dest='indent_with_tabs',
                           help='indent with tabs, overrides -s and -c',
                           default=False)
    style_group.add_option('--close-on-lowest-level',
                           action='store_true',
                           dest='close_on_lowest_level',
                           help='if several closing tokens, indent on lowest token level',
                           default=False)

    style_group.add_option('-F', '--func-cont-level',
                           metavar='N', type='int',
                           dest='func_cont_level',
                           help='continuation lines level in function arguments [' +
                                str(default.func_cont_line_level) + ']',
                           default=default.func_cont_line_level)
    style_group.add_option('-I', '--if-cont-level',
                           metavar='N', type='int',
                           dest='if_cont_line_level',
                           help='if statement continuation line level [2]',
                           default=2)
    style_group.add_option('-M', '--check-line-comment-text',
                           action='store_true',
                           dest='check_space_before_line_comment_text',
                           help='ensure that line comments text is started by at least N char',
                           default=False)
    style_group.add_option('-N', '--com-txt-space-size',
                           metavar='N', type='int',
                           dest='space_before_line_comment_text',
                           help='if --check-line-comment-text is enabled, configure the number of spaces [1]',
                           default=1)
    style_group.add_option('-S', '--skip-sem-colon',
                           action='store_true',
                           dest='skip_semi_colon',
                           help='skip all semi-colon after statements',
                           default=False)
    style_group.add_option('--break-if',
                           action='store_true',
                           dest='break_if_statement',
                           help='break mono-line if statement',
                           default=False)


    style_group.add_option('--strict',
                           action='store_true',
                           dest='strict',
                           help='enable all features',
                           default=False)

    parser.add_option_group(style_group)

    (options, args) = parser.parse_args()

    # generate config
    if options.config_generate:
        Configuration().generate_default('./luastyle.json')
        sys.exit()

    # check argument:
    if not len(args) > 0:
        abort('Expected a filepath or a directory path')

    # handle options:
    if options.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:\t%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    # Configuration from file or cli
    indent_options = None
    # Try to load a config file from default location
    default_filepath = [os.path.join(os.path.expanduser('~'), '.luastylerc')]
    env_var = os.environ.get('LUASTYLE_CONF')
    if env_var is not None:
        default_filepath.append(env_var)
    for filepath in default_filepath:
        if os.path.exists(filepath):  # try to load existing file
            try:
                indent_options = Configuration().load(filepath)
                print('Configuration successfully loaded from ' + filepath)
                break
            except Exception as e:
                abort('Error while reading ' + filepath + ': ' + str(e))
    # then if no file found in default location
    if indent_options is not None and options.config_file:
        if os.path.exists(options.config_file):
            try:
                indent_options = Configuration().load(options.config_file)
            except Exception as e:
                abort('Error while reading ' + options.config_file + ': ' + str(e))
        else:
            abort('Config file doesn''t exist: ' + options.config_file)
    else:
        indent_options = IndentOptions()
        indent_options.indent_size = options.indent_size
        indent_options.indent_char = options.indent_char
        indent_options.indent_with_tabs = options.indent_with_tabs
        indent_options.initial_indent_level = options.initial_indent_level

        indent_options.func_cont_line_level = options.func_cont_level

        indent_options.check_space_before_line_comment_text = options.check_space_before_line_comment_text or options.strict
        indent_options.space_before_line_comment_text = options.space_before_line_comment_text or options.strict
        indent_options.space_around_assign = options.space_around_assign
        indent_options.check_param_list = options.check_param_list or options.strict
        indent_options.check_field_list = options.check_field_list or options.strict
        indent_options.skip_semi_colon = options.skip_semi_colon or options.strict
        indent_options.if_cont_line_level = options.if_cont_line_level
        indent_options.break_if_statement = options.break_if_statement or options.strict
        indent_options.close_on_lowest_level = options.close_on_lowest_level

    # build a filename list
    filenames = []
    if not os.path.isdir(args[0]):
        filenames.append(args[0])
    else:
        for root, subdirs, files in os.walk(args[0]):
            for filename in files:
                if not options.extensions or filename.endswith(tuple(options.extensions)):
                    filepath = os.path.join(root, filename)
                    filenames.append(filepath)

    # process files
    FilesProcessor(options.replace, options.jobs, indent_options).run(filenames)


if __name__ == '__main__':
    main()
