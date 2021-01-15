import os
import numpy as np
import functools

from . import dpath, chunks, resolve_symbols, namespace_dir, group_blocks_into_fills, write_fill


def generate(settings):
    """
    Generates functions that create rings,
    one for each combination of `radiuses` and `blocks_and_tags`.
    """

    radiuses = dpath.get(settings, '/radiuses')

    max_radius = functools.reduce(lambda a, b: max(a, b), radiuses)

    # Generate multiple points on the ring with granularity based on the largest radius.
    points = [
        (np.sin(azimuth), np.cos(azimuth))
        for azimuth in np.arange(-np.pi, np.pi, 0.5 / max_radius)
    ]

    namespace = namespace_dir(settings)

    max_commands = dpath.get(settings, '/max_commands')

    def create_ring_fills(radius):
        """
        Closure on `points` that creates a list of fills for a ring with a given radius.
        """
        print(f'preparing ring: {radius}')

        # convert `points` to `pixels` and remove duplicates
        pixels = (np.array(points) * radius).astype(np.int16)

        # remove duplicates
        uniquePixels = {(x, z) for x, z in pixels}

        # group blocks into fills

        print(f'grouping ring: {radius}')

        blocks = []
        min_x, min_z, max_x, max_z = (0, 0, 0, 0)

        for x, z in uniquePixels:
            min_x = min(min_x, x)
            min_z = min(min_z, z)
            max_x = max(max_x, x + 1)
            max_z = max(max_z, z + 1)
            blocks.append((x, 0, z, True))

        return group_blocks_into_fills(
            blocks, (max_x, 1, max_z), (min_x, 0, min_z)
        )

    def write_ring_function(radius, block, tag, fills):
        """
        Closure that creates a ring function from a list of fills for given radius and block.
        """

        # minecraft functions can only execute `max_commands` commands,
        # so we may have to split functions
        for i, fills_chunk in enumerate(chunks(fills, max_commands)):
            if i > 0:
                tag = f'{tag}_{i}'
            file_name = os.path.join(namespace, f'{radius}_{tag}.mcfunction')
            print(f'writing {file_name}')
            with open(file_name, 'w') as file:
                for min_voxel, max_voxel, _ in fills_chunk:
                    write_fill(file, min_voxel, max_voxel, block)

    # create a ring function for each combination of `radiuses` and `blocks_and_tags`

    blocks_and_tags = [
        (resolve_symbols(settings, block), tag)
        for block, tag in dpath.get(settings, '/blocks_and_tags')
    ]

    for radius in radiuses:
        fills = create_ring_fills(radius)
        for block, tag in blocks_and_tags:
            write_ring_function(radius, block, tag, fills)
