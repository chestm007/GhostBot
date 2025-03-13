from distutils.core import setup

from setuptools import find_packages

setup(
    name='GhostBot',
    version='0.0.1-dev',
    packages=find_packages(),
    url='https://github.com/chestm007/GhostBot',
    license='GPL-2.0',
    author='Max Chesterfield',
    author_email='chestm007@hotmail.com',
    maintainer='Max Chesterfield',
    maintainer_email='chestm007@hotmail.com',
    description='',
    long_description='',
    install_requires=[
        'pymem',
        'npyscreen',
        'windows-curses',
        'pywin32',
        'attrdict',
    ],
    extras_require={},
    entry_points='ghost-bot:Ghostbot.UX.main.py',
)
