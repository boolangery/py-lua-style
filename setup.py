from setuptools import setup

__version__ = '1.0'

setup(name='luastyle',
    version=__version__,
    description='A lua code formatter in Python !',
    url='https://github.com/boolangery/py-lua-formatter',
    download_url = 'https://github.com/boolangery/py-lua-style/archive/' + __version__ + '.tar.gz',
    author='Eliott Dumeix',
    author_email='',
    license='MIT',
    packages=['luastyle', 'luastyle.rules', 'luastyle.tests'],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=['luaparser<=1.1.1'],
    entry_points={
        'console_scripts': [
            'luastyle = luastyle.__main__:main'
        ]
    }
)