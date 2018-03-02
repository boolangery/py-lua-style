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

Usage: luastyle [options] filename

.. code-block::

    CLI Options:
      --version                     Show program's version number and exit
      -h, --help                    Show this help message and exit
      -r, --replace                 Write output in-place, replacing input
      --config=F                    Path to config file
      --config-generate             Generate a default config file
      --type=EXT                    File extension to indent (can be repeated) [lua]
      -d, --debug                   Enable debugging messages
      -j N, --jobs=N                Number of parallel jobs in recursive mode

    Beautifier Options:
      -s N, --indent-size=N         Indentation size [2]
      -c S, --indent-char=S         Indentation character [" "]
      -t, --indent-with-tabs        Indent with tabs, overrides -s and -c
      -l N, --indent-level=N        Initial indentation level [0]
      -A N, --assign-cont-level=N   Continuation lines level in assignment [1]
      -F N, --func-cont-level=N     Continuation lines level in function arguments [2]
      -C, --comma-check             Check spaces after comma
      -R, --indent-return           Indent return continuation lines on next level

      -m, --check-line-comment      Ensure that line comments are separated by at least N char from left sentence
      -n N, --com-space-size=N      If --check-line-comment is enabled, configure the number of spaces [1]
      -M, --check-line-comment-text Ensure that line comments text is started by at least N char
      -N N, --com-txt-space-size=N  If --check-line-comment-text is enabled, configure the number of spaces [1]


Loading settings from environment or .luastylerc
------------------------------------------------------------------------------

In addition to CLI arguments, you may pass a config file via:

- the LUASTYLE_CONF environment variables pointing to a config file
- a .luastylerc file located in your user directory


Options examples
------------------------------------------------------------------------------

Continuation lines level in assignment (-A)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    -A N, --assign-cont-level=N Continuation lines level in assignment [1]

With this raw source code:

.. code-block:: lua

    local errorMessage = 'The process number ' .. tostring(process) ..
      ' generated an exception while processing raw data: ' ..
      processor:getRawData()


.. code-block:: lua

    -- luastyle -c "." -A 0 source.lua

    local errorMessage = 'The process number ' .. tostring(process) ..
    ' generated an exception while processing raw data: ' ..
    processor:getRawData()

.. code-block:: lua

    -- luastyle -c "." -A 2 source.lua

    local errorMessage = 'The process number ' .. tostring(process) ..
    ....' generated an exception while processing raw data: ' ..
    ....processor:getRawData()


Continuation lines level in function arguments (-F)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    -F N, --func-cont-level=N   Continuation lines level in function arguments [2]

With:

.. code-block:: lua

    local function process(param_1, param_2, param_3,
      param_4, param_5, param_6)
      return do_something()
    end


.. code-block:: lua

    -- luastyle -c "." -F 2 source.lua (default value)

    local function process(param_1, param_2, param_3,
    ....param_4, param_5, param_6)
    ..return do_something()
    end

Comments formatting options (-m, -n, -M, -N)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Available options are:

.. code-block::

    -m, --check-line-comment      Ensure that line comments are separated by at least N char from left sentence
    -n N, --com-space-size=N      If --check-line-comment is enabled, configure the number of spaces [1]
    -M, --check-line-comment-text Ensure that line comments text is started by at least N char
    -N N, --com-txt-space-size=N  If --check-line-comment-text is enabled, configure the number of spaces [1]

With this raw source code:

.. code-block:: lua

    --Lorem ipsum dolor sit amet
    local foo--In sodales elit id orci mollis varius


.. code-block:: lua

    -- luastyle -m -n 2 -M -N 1 source.lua

    -- Lorem ipsum dolor sit amet
    local foo  -- In sodales elit id orci mollis varius









