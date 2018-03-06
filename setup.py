from setuptools import setup
import luastyle

setup(
    name='luastyle',
    version=luastyle.__version__,
    description='A lua code formatter in Python !',
    url='https://github.com/boolangery/py-lua-formatter',
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
    install_requires=['luaparser<=1.2.1'],
    entry_points={
        'console_scripts': [
            'luastyle = luastyle.__main__:main'
        ]
    }
)

