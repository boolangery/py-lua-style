import sys
from setuptools import setup, Extension
from distutils.command.sdist import sdist
from distutils.command.build_ext import build_ext
import distutils.cmd
import luastyle


with open('README.rst') as file:
    long_description = file.read()


pyx_ext_modules = [Extension("luastyle.indenter",
                             sources=["luastyle/indenter.pyx", "luastyle/indenter.pxd"],
                             language='c++')]

ext_modules = [Extension('luastyle.indenter',
                         sources=['luastyle/indenter.cpp'],
                         libraries=["stdc++"],
                         extra_compile_args=['-std=c++11'],
                         include_dirs=[],
                         define_macros=[])]


class BuildExt(build_ext):
    def run(self):
        #import Cython
        #import Cython.Build
        #Cython.Build.cythonize(pyx_ext_modules, verbose=True)
        build_ext.run(self)


class CythonizeCommand(distutils.cmd.Command):
  description = 'Cythonize cython files'
  user_options = []

  def initialize_options(self):
      pass

  def finalize_options(self):
      pass

  def run(self):
    import Cython.Build
    Cython.Build.cythonize(pyx_ext_modules, verbose=True)


class Sdist(sdist):
    def __init__(self, *args, **kwargs):
        import Cython.Build
        Cython.Build.cythonize(pyx_ext_modules, verbose=True)
        sdist.__init__(self, *args, **kwargs)


setup(
    name='luastyle',
    version=luastyle.__version__,
    description='A lua code formatter in Python !',
    long_description=long_description,
    url='https://github.com/boolangery/py-lua-style',
    download_url='https://github.com/boolangery/py-lua-style/archive/' + luastyle.__version__ + '.tar.gz',
    author='Eliott Dumeix',
    author_email='eliott.dumeix@gmail.com',
    license='MIT',
    packages=['luastyle', 'luastyle.tests'],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=['luaparser>=2.0'],
    entry_points={
        'console_scripts': [
            'luastyle = luastyle.__main__:main'
        ]
    },
    ext_modules=ext_modules,
    cmdclass={
        'build_ext': BuildExt,
        'sdist': Sdist,
        'cythonize': CythonizeCommand,
    }
)
