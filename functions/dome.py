#!/usr/bin/env python3
"""
Script to create a set of minecraft functions that builds domes, one for each combination of
`radiuses` and `dome_blocks_and_tags`.

Usage:
    dome.py <config-url>...
    dome.py (-h | --help)

Options:
    -h, --help     Show a brief usage summary.

The <config-url> positional arguments should be URLs to a configuration file. If the URL lacks a
scheme, the "file" scheme is assumed. Supported schemes are "https", "file" and "gs". The "gs"
scheme allows configuration contained within a Google Storage bucket to be specified in the same
way as with the "gsutil" command. If multiple configuration files are provided, the specifications
are *deep merged*.
"""
import os
import re
import docopt
import geddit
import yaml
import numpy as np
import functools
import dpath.util as dpath


def check_bounds(voxels):
    """gives the bounds for a list of Voxels"""
    bounds = functools.reduce(
        lambda bounds, voxel: (
            min(bounds[0], voxel[0]), max(bounds[1], voxel[0]),
            min(bounds[2], voxel[1]), max(bounds[3], voxel[1]),
            min(bounds[4], voxel[2]), max(bounds[5], voxel[2]),
        ),
        voxels, (0, 0, 0, 0, 0, 0)
    )
    print(bounds)


def chunks(lst, n):
    """yield successive n-sized chunks from lst"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def load_settings(urls):
    settings = {}
    for url in urls:
        print('Loading settings from %s', url)
        settings = dpath.merge(settings, yaml.safe_load(geddit.geddit(url)))
    return settings


def main():
    opts = docopt.docopt(__doc__)

    # read the settings
    settings = load_settings(opts['<config-url>'])

    print('Generating multiple points')

    # Generate multiple points on the dome with `step` granularity.
    step = 0.002
    points = [
        (
            np.sin(azimuth) * np.cos(elevation),
            np.cos(azimuth) * np.cos(elevation),
            np.sin(elevation)
        )
        # full circle
        for azimuth in np.arange(-np.pi, np.pi, step)
        # from just below the ground to the apex
        for elevation in np.arange(-np.pi/4, np.pi/2, step)
    ]

    # make the namespace dir, if necessary
    namespace = os.path.join(os.getcwd(), dpath.get(settings, '/namespace'))
    os.makedirs(namespace, exist_ok=True)

    max_commands = dpath.get(settings, '/max_commands')

    def create_dome_function(radius, block, tag):
        """
        Closure on `points` that creates a dome function from a block with a given radius.
        """

        # convert `points` to `voxels` and remove duplicates
        voxels = (np.array(points) * radius).astype(np.int16)
        uniqueVoxels = list({(x, y, z) for x, y, z in voxels})

        # minecraft functions can only execute MAX_COMMANDS commands,
        # so we may have to split functions
        for i, chunk in enumerate(chunks(uniqueVoxels, max_commands)):
            if i > 0:
                tag = f'{tag}_{i}'
            file_name = os.path.join(namespace, f'{radius}_{tag}.mcfunction')
            print(file_name)
            with open(file_name, 'w') as file:
                for x, y, z in chunk:
                    # in minecraft, the y axis is vertical (non-intuitively)
                    file.write(f'setblock ~{x} ~{z} ~{y} {block}\n')

    symbol_map = dpath.get(settings, '/symbol_map', default={})

    def resolve_symbols(block):
        """
        Resolve any reference symbols in a block name.
        """
        for brace in re.findall(r'{.*?}', block):
            block = block.replace(brace, symbol_map[brace[1:-1]])
        return block

    # create a dome function for each combination of `radiuses` and `blocks_and_tags`
    blocks_and_tags = [
        (resolve_symbols(block), tag)
        for block, tag in dpath.get(settings, '/blocks_and_tags')
    ]

    for radius in dpath.get(settings, '/radiuses'):
        for block, tag in blocks_and_tags:
            create_dome_function(radius, block, tag)


if __name__ == "__main__":
    main()
