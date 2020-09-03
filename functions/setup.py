import os

from setuptools import setup, find_packages


def load_requirements():
    """
    Load requirements file and return non-empty, non-comment lines with leading and trailing
    whitespace stripped.
    """
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
        return [
            line.strip() for line in f
            if line.strip() != '' and not line.strip().startswith('#')
        ]


setup(
    name='minecraftfunctions',
    version='0.0.1',
    packages=find_packages(),
    install_requires=load_requirements(),
    entry_points={
        'console_scripts': [
            'minecraftfunctions=functions.__main__:main',
        ]
    }
)
