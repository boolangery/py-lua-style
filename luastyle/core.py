#!/usr/bin/env python3
import sys
import os
import logging
import time
import configparser
import luastyle.rules
import concurrent.futures

class ConfigurationReader():
    FILENAME = 'luastyle.conf'

    def writeDefault(self):
        indentDefaultOption = luastyle.rules.IndentOptions()
        config = configparser.ConfigParser()

        config['INDENTATION'] = {
            'IndentType': self.indentType.value,
            'IndentSize': self.indentSize,
            'AssignementContinuationLineLevel': self.assignContinuationLineLevel,
            'FunctionContinuationLineLevel': self.functionContinuationLineLevel,
        }

        filepath = os.path.join(os.path.expanduser("~"), FILENAME)
        with open(filepath, 'w') as configfile:
            config.write(configfile)

        # config = None
        # for loc in os.curdir, os.path.expanduser("~"), "/etc/luastyle", os.environ.get("LUASTYLE_CONF"):
        #     try:
        #         with open(os.path.join(loc, "myproject.conf")) as source:
        #             config.readfp(source)
        #     except IOError:
        #         pass

class FilesProcessor():
    def __init__(self, rules, rewrite, jobs):
        self._rules = rules
        self._rewrite = rewrite
        self._jobs = jobs

    def _processOne(self, filepath):
        """Process one file.
        """
        with open(filepath) as file:
            rule_input = file.read()
        rule_output = rule_input
        for rule in self._rules:
            logging.debug('Applying ' + rule.__class__.__name__)
            rule_output = rule.apply(rule_output)

        if self._rewrite:
            f = open(filepath, 'r+')
            f.seek(0)
            f.write(rule_output)
            f.truncate()
            f.close()

        return len(rule_output.split('\n'))

    def run(self, files):
        print(str(len(files)) + ' file(s) to process')

        processed = 0
        print('[' + str(processed) + '/' + str(len(files)) + '] file(s) processed')

        # some stats
        start = time.time()
        total_lines = 0

        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ThreadPoolExecutor(max_workers=self._jobs) as executor:
            # Start process operations and mark each future with its filename
            future_to_file = {executor.submit(self._processOne, file): file for file in files}
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    total_lines += future.result()
                except Exception as exc:
                    print('%r generated an exception: %s' % (file, exc))
                else:
                    processed += 1
                    print('[' + str(processed) + '/' + str(len(files)) + '] file(s) processed, last is ' + file)
                    sys.stdout.flush()

        end = time.time()
        print(str(total_lines) + ' source lines processed in ' + str(round(end - start, 2)) + ' s')
