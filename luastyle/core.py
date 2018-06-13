import os
import sys
import time
import subprocess
import concurrent.futures
from tempfile import mkstemp

from luastyle.indenter import IndentRule, IndentOptions


class BytecodeException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(BytecodeException, self).__init__(message)

class Configuration:
    def load(self, filepath):
        with open(filepath) as json_data_file:
            content = json_data_file.read()
        options = IndentOptions.from_json(content)
        return options

    def generate_default(self, filepath):
        with open(filepath, 'w') as json_data_file:
            json_data_file.write(IndentOptions().to_json())
        print('Config. file generated in: ' + os.path.abspath(filepath))


class FilesProcessor:
    def __init__(self, rewrite, jobs, check_bytecode, indent_options):
        self._rewrite = rewrite
        self._jobs = jobs
        self._check_bytecode = check_bytecode
        self._indent_options = indent_options

    def _process_one(self, filepath):
        """Process one file.
        """
        with open(filepath) as file:
            rule_input = file.read()

        rule_output = IndentRule(self._indent_options).apply(rule_input)

        if self._check_bytecode:
            bytecode_equal = check_lua_bytecode(rule_input, rule_output)
        else:
            bytecode_equal = True

        if bytecode_equal:
            if self._rewrite:
                f = open(filepath, 'r+')
                f.seek(0)
                f.write(rule_output)
                f.truncate()
                f.close()
            else:
                print(rule_output)

        return bytecode_equal, len(rule_output.split('\n'))

    def run(self, files):
        print(str(len(files)) + ' file(s) to process')

        processed = 0
        print('[' + str(processed) + '/' + str(len(files)) + '] file(s) processed')

        # some stats
        start = time.time()
        total_lines = 0

        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ProcessPoolExecutor(max_workers=self._jobs) as executor:
            # Start process operations and mark each future with its filename
            future_to_file = {executor.submit(self._process_one, file): file for file in files}
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    success, n_lines = future.result()
                    total_lines += n_lines
                    if not success:
                        raise BytecodeException('bytecode differs')
                except Exception as exc:
                    print('%r generated an exception: %s' % (file, exc))
                else:
                    processed += 1
                    print('[' + str(processed) + '/' + str(len(files)) + '] file(s) processed, last is ' + file)
                    sys.stdout.flush()

        end = time.time()
        print(str(total_lines) + ' source lines processed in ' + str(round(end - start, 2)) + ' s')


def check_lua_bytecode(raw, formatted):
    if os.name == 'nt':
        raise NotImplementedError('check_lua_bytecode not supported on windows')
    else:
        fd, raw_path = mkstemp()
        fd, formatted_path = mkstemp()
        fd, raw_bytecode = mkstemp()
        fd, formatted_bytecode = mkstemp()

        # create raw file
        with open(raw_path, 'w') as file:
            file.write(raw)

        # create formatted file
        with open(formatted_path, 'w') as file:
            file.write(formatted)

        # compile files, strip
        if 'LUAC' in os.environ:
            luac = '$LUAC'
        else:
            luac = 'luac'

        os.system(luac + ' -s -o ' + raw_bytecode + ' ' + raw_path)
        os.system(luac + ' -s -o ' + formatted_bytecode + ' ' + formatted_path)

        # check diff
        # This command could have multiple commands separated by a new line \n
        some_command = 'diff ' + raw_bytecode + ' ' + formatted_bytecode
        p = subprocess.Popen(some_command, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        # This makes the wait possible
        p_status = p.wait()

        output = output.decode("utf-8")


        bytecode_equal = (p_status == 0) and (output == "")

        # cleanup
        os.remove(raw_path)
        os.remove(formatted_path)
        os.remove(raw_bytecode)
        os.remove(formatted_bytecode)

        return bytecode_equal
