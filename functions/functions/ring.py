import os
import numpy as np

from . import dpath, chunks, resolve_symbols


def generate(settings):
    """
    Generates functions that create rings,
    one for each combination of `radiuses` and `blocks_and_tags`.
    """
    # Generate multiple points on the dome with `step` granularity.
    step = 0.002
    points = [
        (np.sin(azimuth), np.cos(azimuth), 0)
        for azimuth in np.arange(-np.pi, np.pi, step)
    ]

    # make the namespace dir, if necessary
    namespace = os.path.join(
        dpath.get(settings, '/output_path'), dpath.get(settings, '/namespace')
    )
    os.makedirs(namespace, exist_ok=True)

    max_commands = dpath.get(settings, '/max_commands')

    def create_ring_function(radius, block, tag):
        """
        Closure on `points` that creates a dome function from a block with a given radius.
        """

        # convert `points` to `voxels` and remove duplicates
        voxels = (np.array(points) * radius).astype(np.int16)
        uniqueVoxels = list({(x, y, z) for x, y, z in voxels})

        # minecraft functions can only execute `max_commands` commands,
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

    # create a ring function for each combination of `radiuses` and `blocks_and_tags`
    blocks_and_tags = [
        (resolve_symbols(settings, block), tag)
        for block, tag in dpath.get(settings, '/blocks_and_tags')
    ]

    for radius in dpath.get(settings, '/radiuses'):
        for block, tag in blocks_and_tags:
            create_ring_function(radius, block, tag)
