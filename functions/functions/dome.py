import os
import numpy as np
import functools

from . import dpath, chunks, resolve_symbols, namespace_dir, group_blocks_into_fills, write_fill


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

    radiuses = dpath.get(settings, '/radiuses')

    # Generate multiple points on the dome with based on the largest radius.

    step = 0.5 / functools.reduce(lambda a, b: max(a, b), radiuses)

    points = [
        (
            np.sin(azimuth) * np.cos(elevation),
            np.sin(elevation),
            np.cos(azimuth) * np.cos(elevation),
        )
        # full circle
        for azimuth in np.arange(-np.pi, np.pi, step)
        # from just below the ground to the apex
        for elevation in np.arange(-np.pi/4, np.pi/2, step)
    ]

    def create_dome_fills(radius):
        """
        Closure on `points` that creates a list of fills for a dome with a given radius.
        """
        print(f'preparing dome: {radius}')

        # convert `points` to `voxels` and remove duplicates
        voxels = (np.array(points) * radius).astype(np.int16)

        # remove duplicates
        uniqueVoxels = {(x, y, z) for x, y, z in voxels}

        # group blocks into fills

        print(f'grouping dome: {radius}')

        blocks = []
        min_x, min_y, min_z = (0, 0, 0)
        max_x, max_y, max_z = (0, 0, 0)

        for x, y, z in uniqueVoxels:
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            min_z = min(min_z, z)
            max_x = max(max_x, x + 1)
            max_y = max(max_y, y + 1)
            max_z = max(max_z, z + 1)
            blocks.append((x, y, z, True))

        return group_blocks_into_fills(
            blocks, (max_x, max_y, max_z), (min_x, min_y, min_z)
        )

    def write_dome_function(radius, block, tag, fills):
        """
        Closure that creates a dome function from a list of fills for given radius and block.
        """
        # minecraft functions can only execute MAX_COMMANDS commands,
        # so we may have to split functions
        for i, fills_chunk in enumerate(chunks(fills, max_commands)):
            if i > 0:
                tag = f'{tag}_{i}'
            file_name = os.path.join(namespace, f'{radius}_{tag}.mcfunction')
            print(f'writing {file_name}')
            with open(file_name, 'w') as file:
                for min_voxel, max_voxel, _ in fills_chunk:
                    write_fill(file, min_voxel, max_voxel, block)

    # create a dome function for each combination of `radiuses` and `blocks_and_tags`

    blocks_and_tags = [
        (resolve_symbols(settings, block), tag)
        for block, tag in dpath.get(settings, '/blocks_and_tags')
    ]

    for radius in radiuses:
        fills = create_dome_fills(radius)
        for block, tag in blocks_and_tags:
            write_dome_function(radius, block, tag, fills)
