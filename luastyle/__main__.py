#!/usr/bin/env python3
import sys
import os
import logging
from optparse import OptionParser
from luastyle.core import FilesProcessor
from luastyle.indent import IndentOptions

def abort(msg):
    logging.error(msg)
    sys.exit()

def main():
    # parse options:
    usage = 'usage: %prog [options] file|directory'
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--debug', action='store_true',  dest='debug', help='enable debugging messages', default=False)
    parser.add_option('-s', '--simu', action='store_true', dest='simu', help='do not rewrite file (simulation)', default=False)
    parser.add_option('-r', '--recursive', action='store_true',  dest='recursive', help='indent all files in directory', default=False)
    parser.add_option('-e', '--extensions', action="append", type="string", dest='extensions', metavar='EXT',
                      help='file extension to keep in recursive mode (can be repeated)', default=[])
    # multi-threading
    parser.add_option('-j', '--jobs', metavar='NUMBER', type="int",  dest='jobs', help='number of parallel jobs in recursive mode', default=4)
    # optional rules
    parser.add_option('--with-table-align', action='store_true',  dest='tableAlign', help='enable table alignment', default=False)
    # indentRule options:
    default = IndentOptions()
    parser.add_option('--with-indent-value', metavar='NUMBER', type="int", dest='indentValue', help='configure the number of whitespace per indentation level', default=2)
    parser.add_option('--with-assign-cont-level', metavar='NUMBER', type="int", dest='assignContLevel',
                      help='configure the level of continuation lines in assign', default=default.assignContinuationLineLevel)
    parser.add_option('--with-func-cont-level', metavar='NUMBER', type="int", dest='funcContLevel',
                      help='configure the level of continuation lines in function arguments',
                      default=default.functionContinuationLineLevel)
    parser.add_option('--with-comma-check', action='store_true', dest='commaCheck', help='check spaces after comma',
                      default=default.checkSpaceAfterComma)

    (options, args) = parser.parse_args()
    # check argument:
    if not len(args) > 0:
        abort('Expected a path')
    if not os.path.exists(args[0]):
        abort('File ' + sys.argv[1] + ' doesn\'t exists')
    if options.recursive:
        if not os.path.isdir(args[0]):
            abort('Must be a directory (-r option)')

    # handle options:
    if options.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:\t%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    # IndentRule options:
    indentOptions = IndentOptions()
    indentOptions.indentSize = options.indentValue
    indentOptions.assignContinuationLineLevel = options.assignContLevel
    indentOptions.functionContinuationLineLevel = options.funcContLevel
    indentOptions.checkSpaceAfterComma = options.commaCheck

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
    FilesProcessor(not options.simu, options.jobs, indentOptions).run(filenames)

if __name__ == '__main__':
    main()
