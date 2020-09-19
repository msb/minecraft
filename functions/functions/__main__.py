"""
Script to create a set of minecraft functions depending on the generator selected and the
configuration supplied.

Usage:
    minecraftfunctions structure <nbt-file> <function-file>
    minecraftfunctions <generator> <config-url>...
    minecraftfunctions (-h | --help)

Options:
    -h, --help     Show a brief usage summary.

The <config-url> positional arguments should be URLs to a configuration file. If the URL lacks a
scheme, the "file" scheme is assumed. Supported schemes are "https", "file" and "gs". The "gs"
scheme allows configuration contained within a Google Storage bucket to be specified in the same
way as with the "gsutil" command. If multiple configuration files are provided, the specifications
are *deep merged*.

Generators:

    minecraftfunctions structure ...

        Converts an NBT structure file into an mcfunction file.

    minecraftfunctions dome ...

        Generates functions that create domes,
        one for each combination of `radiuses` and `blocks_and_tags`.

    minecraftfunctions ring ...

        Generates functions that create rings,
        one for each combination of `radiuses` and `blocks_and_tags`.

    minecraftfunctions cloudtree ...

        Generates functions that create Cloud (very big) Trees.

    minecraftfunctions maze ...

        Generates functions to create a maze.
"""
import docopt
import yaml
import geddit
import sys

from . import dpath

# all generators are statically linked here
from .dome import generate as generate_dome  # noqa F401
from .ring import generate as generate_ring  # noqa F401
from .cloudtree import generate as generate_cloudtree  # noqa F401
from .maze import generate as generate_maze  # noqa F401

from .structure import generate as generate_structure


def load_settings(urls):
    """Loads a set of YAML configuration files and deep merges then into a single dict."""
    settings = {}
    for url in urls:
        print(f'Loading settings from {url}')
        settings = dpath.merge(settings, yaml.safe_load(geddit.geddit(url)))
    return settings


def main():
    opts = docopt.docopt(__doc__)

    if opts['structure']:
        generate_structure(opts['<nbt-file>'], opts['<function-file>'])
    else:
        try:
            generator = getattr(sys.modules[__name__], f"generate_{opts['<generator>']}")
        except AttributeError:
            sys.exit(f"{opts['<generator>']} is not a generator")

        # read the settings
        settings = load_settings(opts['<config-url>'])

        generator(settings)
