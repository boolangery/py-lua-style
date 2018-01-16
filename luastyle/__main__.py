#!/usr/bin/env python3
import sys
import os
import logging
from optparse import OptionParser
import luastyle.rules


def abort(msg):
    logging.error(msg)
    sys.exit()

def processFile(filepath, rules, rewrite):
    # read whole file:
    logging.info('Working on file ' + filepath)
    input = ''
    with open(filepath) as file:
        input = file.read()

    output = input
    for rule in rules:
        logging.debug('Applying ' + rule.__class__.__name__)
        output = rule.apply(output)

    if not rewrite:
        logging.info('done.')
        logging.debug(output)
    else:
        f = open(filepath, 'r+')
        f.seek(0)
        f.write(output)
        f.truncate()
        f.close()
        logging.info('file rewrited.')

def main():
    # parse options:
    usage = 'usage: %prog [options] filename'
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--debug', action='store_true',  dest='debug', help='enable debugging messages', default=False)
    parser.add_option('-w', '--rewrite', action='store_true',  dest='rewrite', help='rewrite current file', default=False)
    parser.add_option('-r', '--recursive', action='store_true',  dest='recursive', help='indent all files in directory', default=False)
    parser.add_option('--with-table-align', action='store_true',  dest='tableAlign', help='enable table alignment', default=False)
    parser.add_option('--with-indent-value', metavar='NUMBER', type="int", dest='indentValue', help='configure the number of whitespace per indentation level', default=2)
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
    indentOptions = luastyle.rules.IndentOptions()
    indentOptions.indentType = luastyle.rules.IndentType.SPACE
    indentOptions.indentSize = options.indentValue

    # optional rules:
    optionalRules = []
    if options.tableAlign: optionalRules.append(luastyle.rules.AlignTableRule())

    # chaining rules:
    rules = [
        luastyle.rules.IndentRule(indentOptions)] + optionalRules + [
        luastyle.rules.StripRule(),
        luastyle.rules.EndingNewLineRule()]

    if not options.recursive:
        processFile(args[0], rules, options.rewrite)
    else:
        for root, subdirs, files in os.walk(args[0]):
            for filename in files:
                filepath = os.path.join(root, filename)
                processFile(filepath, rules, options.rewrite)

if __name__ == '__main__':
    main()