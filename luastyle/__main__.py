#!/usr/bin/env python3
import sys
import os
import time
import logging
import concurrent.futures
from optparse import OptionParser
from luastyle.core import FilesProcessor
import luastyle.rules

def abort(msg):
    logging.error(msg)
    sys.exit()

def process(filepath, rules, rewrite):
    input = ''
    with open(filepath) as file:
        input = file.read()
    output = input
    for rule in rules:
        logging.debug('Applying ' + rule.__class__.__name__)
        output = rule.apply(output)

    if  rewrite:
        f = open(filepath, 'r+')
        f.seek(0)
        f.write(output)
        f.truncate()
        f.close()

    return len(output.split('\n'))

# multi-threaded
def processFiles(files, rules, rewrite, jobs):
    # We can use a with statement to ensure threads are cleaned up promptly
    print(str(len(files)) + ' file(s) to process')

    processed = 0
    print('[' + str(processed) + '/' + str(len(files)) + '] file(s) processed')

    # some stats
    start = time.time()
    totalLines = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        # Start process operations and mark each future with its filename
        future_to_file = {executor.submit(process, file, rules, rewrite): file for file in files}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                totalLines += future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (file, exc))
            else:
                processed += 1
                print('[' + str(processed) + '/' + str(len(files)) + '] file(s) processed, last is ' + file)
                sys.stdout.flush()

    end = time.time()
    print(str(totalLines) + ' source lines processed in ' + str(round(end - start, 2)) + ' s')

def main():
    # parse options:
    usage = 'usage: %prog [options] filename'
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--debug', action='store_true',  dest='debug', help='enable debugging messages', default=False)
    parser.add_option('-s', '--simu', action='store_true', dest='simu', help='do not rewrite file (simulation)', default=False)
    parser.add_option('-r', '--recursive', action='store_true',  dest='recursive', help='indent all files in directory', default=False)
    # multi-threading
    parser.add_option('-j', '--jobs', metavar='NUMBER', type="int",  dest='jobs', help='number of parallel jobs in recursive mode', default=4)
    # optional rules
    parser.add_option('--with-table-align', action='store_true',  dest='tableAlign', help='enable table alignment', default=False)
    # indentRule options:
    default = luastyle.rules.IndentOptions()
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
    indentOptions = luastyle.rules.IndentOptions()
    indentOptions.indentType = luastyle.rules.IndentType.SPACE
    indentOptions.indentSize = options.indentValue
    indentOptions.assignContinuationLineLevel = options.assignContLevel
    indentOptions.functionContinuationLineLevel = options.funcContLevel
    indentOptions.checkSpaceAfterComma = options.commaCheck

    # optional rules:
    optionalRules = []
    if options.tableAlign: optionalRules.append(luastyle.rules.AlignTableRule())

    # chaining rules:
    rules = [
        luastyle.rules.IndentRule(indentOptions)] + optionalRules + [
        luastyle.rules.StripRule(),
        luastyle.rules.EndingNewLineRule()]

    # build a filename list
    filenames = []
    if not options.recursive:
        filenames.append(args[0])
    else:
        for root, subdirs, files in os.walk(args[0]):
            for filename in files:
                filepath = os.path.join(root, filename)
                filenames.append(filepath)

    # process files
    FilesProcessor(rules, not options.simu, options.jobs).run(filenames)

if __name__ == '__main__':
    main()