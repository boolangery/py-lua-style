import os
import sys
import time
import json
import concurrent.futures
from luastyle.indent import IndentRule, IndentOptions


class Configuration:
    def load(self, filepath):
        with open(filepath) as json_data_file:
            data = json.load(json_data_file)
        options = IndentOptions()
        options.__dict__ = data
        return options

    def generate_default(self, filepath):
        with open(filepath, 'w') as json_data_file:
            json_data_file.write(
                json.dumps(IndentOptions().__dict__,
                           sort_keys=True,
                           indent=4,
                           separators=(',', ': ')))
        print('Config. file generated in: ' + os.path.abspath(filepath))


class FilesProcessor:
    def __init__(self, rewrite, jobs, indent_options):
        self._rewrite = rewrite
        self._jobs = jobs
        self._indent_options = indent_options

    def _process_one(self, filepath):
        """Process one file.
        """
        with open(filepath) as file:
            rule_input = file.read()

        rule_output = IndentRule(self._indent_options).apply(rule_input)

        if self._rewrite:
            f = open(filepath, 'r+')
            f.seek(0)
            f.write(rule_output)
            f.truncate()
            f.close()
        else:
            print(rule_output)

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
            future_to_file = {executor.submit(self._process_one, file): file for file in files}
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
