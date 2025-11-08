from setuptools import find_packages, setup

setup(
    name='GhostBot',
    version='0.0.1',
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
        'pyyaml',
        'pillow',
        'numpy',
        'opencv-python'
    ],
    extras_require={},
    entry_points={
        'console_scripts': [
            'ghost-bot-client = GhostBot.UX.main:main',
            'ghost-bot-server = GhostBot.bot_controller:main',
        ]
    }
)
