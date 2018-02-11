py-lua-style
===============================================================================

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
      --version                   Show program's version number and exit
      -h, --help                  Show this help message and exit
      -r, --replace               Write output in-place, replacing input
      --config=F                  Path to config file
      --config-generate           Generate a default config file
      --type=EXT                  File extension to indent (can be repeated) [lua]
      -d, --debug                 Enable debugging messages
      -j N, --jobs=N              Number of parallel jobs in recursive mode

    Beautifier Options:
      -s N, --indent-size=N       Indentation size [2]
      -c S, --indent-char=S       Indentation character [" "]
      -t, --indent-with-tabs      Indent with tabs, overrides -s and -c
      -l N, --indent-level=N      Initial indentation level [0]
      -A N, --assign-cont-level=N Continuation lines level in assignment [1]
      -F N, --func-cont-level=N   Continuation lines level in function arguments [2]
      -C, --comma-check           Check spaces after comma
      -R, --indent-return         Indent return continuation lines on next level


Loading settings from environment or .luastylerc
------------------------------------------------------------------------------

In addition to CLI arguments, you may pass a config file via:

- the LUASTYLE_CONF environment variables pointing to a config file
- a .luastylerc file located in your user directory


Options examples
------------------------------------------------------------------------------

Continuation lines level in assignment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    -A N, --assign-cont-level=N Continuation lines level in assignment [1]

With:

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


Continuation lines level in function arguments
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
