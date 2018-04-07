from setuptools import setup, find_packages

setup(
    name = 'flimsy',
    version = '0.0.0-dev',
    author = 'Sean Wilson',
    author_email = 'spwilson2@wisc.edu',
    license = 'BSD',
    entry_points=
    '''
    [console_scripts]
    flimsy=flimsy:main
    ''',
    #whimsy.main:main
    packages=find_packages(),
)
