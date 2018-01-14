from setuptools import setup

setup(name='luastyle',
    version='0.1',
    description='A lua code formatter in Python !',
    url='https://github.com/boolangery/py-lua-formatter',
    author='Eliott Dumeix',
    author_email='',
    license='MIT',
    packages=['luastyle', 'luastyle.rules'],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=['luastyle >= 0.1'],
    entry_points={
        'console_scripts': [
            'luastyle = luastyle.__main__:main'
        ]
    }
)