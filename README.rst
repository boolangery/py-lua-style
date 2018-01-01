py-lua-style
===============================================================================

A Lua code formatter written in Python.

Installation:
------------------------------------------------------------------------------

The package can be installed through `pip`:

.. code-block::

    $ git clone https://github.com/boolangery/py-lua-style.git
    $ cd py-lua-style
    $ python3.6 -m pip install .

Usage
------------------------------------------------------------------------------

Usage: luastyle [options] filename

Options:
  -h, --help            show this help message and exit
  -d, --debug           enable debugging messages
  -w, --rewrite         rewrite current file
  -r, --recursive       indent all files in directory
  --with-table-align    enable table alignment
  --with-indent-value=NUMBER
                        configure the number of whitespace per indentation
                        level
