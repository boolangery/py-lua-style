py-lua-style
===============================================================================

.. image:: https://travis-ci.org/boolangery/py-lua-style.svg?branch=master
    :target: https://travis-ci.org/boolangery/py-lua-style
.. image:: https://img.shields.io/pypi/v/luastyle.svg
    :target: https://pypi.python.org/pypi/luastyle/
.. image:: https://img.shields.io/pypi/pyversions/luastyle.svg
    :target: https://pypi.python.org/pypi/luastyle/

A Lua code formatter written in Python.


Installation:
------------------------------------------------------------------------------

The package can be installed through `pip`:

.. code-block::

    $ python3.6 -m pip install luastyle

It will install the shell command 'luastyle'.


Options
------------------------------------------------------------------------------

These are the command-line flags:

Usage: luastyle [options] file_or_dir1 file_or_dir2 ...

.. code-block::

  CLI Options:
    --version                       Show program's version number and exit
    -h, --help                      Show this help message and exit
    -i, --in-place                  Write output in-place, replacing input
    --config=F                      Path to config file
    --config-generate               Generate a default config file
    --type=EXT                      File extension to indent (can be repeated) [lua]
    -d, --debug                     Enable debugging messages
    -j N, --jobs=N                  Number of parallel jobs in recursive mode
    -C, --check-bytecode            Check lua bytecode with luac, $LUAC can also be set to
                                    use a specific compiler


  Beautifier Options:
    -a, --space-around-assign       Ensure one space before and after assign op "="
    -c S, --indent-char=S           Indentation character [" "]
    -f, --check-field-list          Format field-list (table)
    -l N, --indent-level=N          Initial indentation level [0]
    -p, --check-param-list          Format var-list, name-list and expr-list
    -s N, --indent-size=N           Indentation size [2]
    -t, --indent-with-tabs          Indent with tabs, overrides -s and -c
    --close-on-lowest-level         If several closing tokens, indent on lowest token level
    -F N, --func-cont-level=N       Continuation lines level in function arguments [2]
    -I N, --if-cont-level=N         If statement continuation line level [2]
    -M, --check-line-comment-text   Ensure that line comments text is started by at least N char
    -N N, --com-txt-space-size=N    If --check-line-comment-text is enabled, configure the number of spaces [1]
    -S, --skip-sem-colon            Skip all semi-colon after statements
    --break-if                      Break mono-line if statement
    --break-while                   In while and repeat statement, ensure newline after
                                    "do" or "repeat" and before "end" or "until" keyword
    --break-all                     Enable --break-if --break-for and --break-while and
                                    before "end" or "until" keyword
    --force-call-spaces             Force spaces before opening parenthesis in function
                                    call [0]
    --call-spaces-size=N            If --force-call-spaces is enabled, configure the
                                    number of spaces
    --strict                        Enable all features


Loading settings from environment or .luastylerc
------------------------------------------------------------------------------

In addition to CLI arguments, you may pass a config file via:

- the LUASTYLE_CONF environment variables pointing to a config file
- a .luastylerc file located in your user directory


Options examples
------------------------------------------------------------------------------


Continuation lines level in function arguments (-F)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    -F N, --func-cont-level=N   Continuation lines level in function arguments [2]

Given:

.. code-block:: lua

    local function process(param_1, param_2, param_3,
      param_4, param_5, param_6)
      return do_something()
    end

.. code-block:: console

    $ luastyle -c "." -F 2 source.lua

.. code-block:: lua

    local function process(param_1, param_2, param_3,
    ....param_4, param_5, param_6)
    ..return do_something()
    end


Comments formatting options (-M, -N)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Available options are:

.. code-block::

    -M, --check-line-comment-text Ensure that line comments text is started by at least N char
    -N N, --com-txt-space-size=N  If --check-line-comment-text is enabled, configure the number of spaces [1]

Given:

.. code-block:: lua

    --Lorem ipsum dolor sit amet
    local foo --In sodales elit id orci mollis varius


.. code-block:: console

    $ luastyle -M -N 1 source.lua


.. code-block:: lua

    -- Lorem ipsum dolor sit amet
    local foo -- In sodales elit id orci mollis varius


Break If statement option (--break-if)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given:

.. code-block:: lua

    if condition then return success() else return failure() end


.. code-block:: console

    $ luastyle --break-if source.lua


.. code-block:: lua

    if condition then
      return success()
    else
      return failure()
    end


Format table field-list (-f)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This option ensure that:
  * field separator in table (',' or ';') are trailing
  * comma is preceded by one space and followed by two spaces

The keyword '@luastyle.disable' placed in a comment just after the opening brace
will disable this feature in the concerned table.

Given:

.. code-block:: lua

    local days = {
      monday = 1,
      tuesday = 2
    , wednesday = 3
    }

    local n = {1  , 2,3}

    local t = {
      -- @luastyle.disable
      1,    2,    4,
      8,    16,   32
    }


.. code-block:: console

    $ luastyle -f source.lua


.. code-block:: lua

    local days = {
      monday = 1,
      tuesday = 2,
      wednesday = 3
    }

    local n = {1, 2, 3}

    local t = {
      -- @luastyle.disable
      1,    2,    4,
      8,    16,   32
    }



Indent closing token (--close-on-lowest-level )
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given:

.. code-block:: lua

    describe('must indent', function()
      done()
    end)


.. code-block:: console

    $ luastyle --close-on-lowest-level source.lua


.. code-block:: lua

    describe('must indent', function()
        done()
      end)


.. code-block:: console

    $ luastyle source.lua


.. code-block:: lua

    describe('must indent', function()
        done()
    end)

Function call formatting options (--force-call-spaces, --call-spaces-size)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given:

.. code-block:: lua

    build (foo)


.. code-block:: console

    $ luastyle --force-call-spaces source.lua


.. code-block:: lua

    build(foo)

.. code-block:: console

    $ luastyle --force-call-spaces --call-spaces-size=1 source.lua


.. code-block:: lua

    build (foo)
