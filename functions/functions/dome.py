import os
import numpy as np
import functools

from . import dpath, chunks, resolve_symbols, namespace_dir


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


def generate(settings):
    """
    Generates functions that create domes,
    one for each combination of `radiuses` and `blocks_and_tags`.
    """
    namespace = namespace_dir(settings)

    max_commands = dpath.get(settings, '/max_commands')

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

    # create a dome function for each combination of `radiuses` and `blocks_and_tags`
    blocks_and_tags = [
        (resolve_symbols(settings, block), tag)
        for block, tag in dpath.get(settings, '/blocks_and_tags')
    ]

    for radius in dpath.get(settings, '/radiuses'):
        for block, tag in blocks_and_tags:
            create_dome_function(radius, block, tag)
