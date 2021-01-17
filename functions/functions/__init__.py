import os
import re
import dpath.util as dpath


def chunks(lst, n):
    """yield successive n-sized chunks from lst"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def resolve_symbols(settings, block):
    """
    Resolve any reference symbols in a block name.
    """
    symbol_map = dpath.get(settings, '/symbol_map', default={})

    for brace in re.findall(r'{.*?}', block):
        block = block.replace(brace, symbol_map[brace[1:-1]])
    return block


def namespace_dir(settings):
    """Combine `output_path` & `namespace` to form the output dir."""
    namespace = os.path.join(
        dpath.get(settings, '/output_path'), dpath.get(settings, '/namespace')
    )
    # make the namespace dir, if necessary
    os.makedirs(namespace, exist_ok=True)

    return namespace


def group_blocks_into_fills(blocks, max_size, min_size=(0, 0, 0)):
    """
    A 'good enough' function that groups similar blocks into fills where possible.

    `blocks` is an array of (x, y, z, name) tuples where `name` can be any type that defines a
    block (eg. if all the blocks are the same then `name` could just be `True`). `max_size` is a
    voxel tuple defining the size of the volume the blocks are bound by. If blocks have negative
    voxels `min_size` is used to define the minimum bounds of the volume - eg. two blocks (1, 1, 1)
    and (-1, -1, -1) would be bound by `min_size=(-1, -1, -1)` and `max_size=(2, 2, 2)`.

    An array of ((min_x, min_y, min_z), (max_x, max_y, max_z), name) tuples is returned. If a block
    couldn't be grouped then the min and max voxels will be equivalent.
    """

    # create ranges for iterating over the volume occupied by the block (indexed from 0)
    range_x, range_y, range_z = [
        range(max_coord - min_coord) for min_coord, max_coord in zip(min_size, max_size)
    ]

    # initialise a 3D array with block values

    volume = [[[None for z in range_z] for y in range_y] for x in range_x]

    min_size_x, min_size_y, min_size_z = min_size

    for x, y, z, name in blocks:
        volume[x - min_size_x][y - min_size_y][z - min_size_z] = name

    def group_blocks(min_x, min_y, min_z):
        """
        From a particular block within the volume, try to match with adjacent (and higher) matching
        blocks to form a fill which is returned. At a minimum the block itself is returned.
        Any blocks returned are removed from the volume.
        """
        # this is the block to match
        name = volume[min_x][min_y][min_z]

        # group all matching contiguous blocks in the `x` direction
        max_x = min_x + 1
        while max_x in range_x and volume[max_x][min_y][min_z] == name:
            max_x += 1

        # group all matching contiguous blocks in the `y` direction
        max_y = min_y + 1
        while max_y in range_y:
            match = all(
                volume[x][max_y][min_z] == name
                for x in range(min_x, max_x)
            )
            if not match:
                break
            max_y += 1

        # group all matching contiguous blocks in the `z` direction
        max_z = min_z + 1
        while max_z in range_z:
            match = all(
                volume[x][y][max_z] == name
                for x in range(min_x, max_x)
                for y in range(min_y, max_y)
            )
            if not match:
                break
            max_z += 1

        # Remove the grouped blocks from the volume.
        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                for z in range(min_z, max_z):
                    volume[x][y][z] = None

        return (
            (min_size_x + min_x, min_size_y + min_y, min_size_z + min_z),
            (min_size_x + max_x - 1, min_size_y + max_y - 1, min_size_z + max_z - 1),
            name
        )

    # iterate over the volume in an ascending direction and when a block is encountered, try to
    # group it with blocks in the same direction to form a fill.

    fills = []

    for x in range_x:
        for y in range_y:
            for z in range_z:
                if volume[x][y][z]:
                    fills.append(group_blocks(x, y, z))
    return fills


def write_fill(function_file, min_voxel, max_voxel, block, origin=(0, 0, 0)):
    """
    Writes a fill (or setblock) command to `function_file` for a given volume.
    An optional origin can be supplied to adjust the offset the position.
    """
    min_x, min_y, min_z = min_voxel
    x, y, z = origin
    min_set = f'~{min_x - x} ~{min_y - y} ~{min_z - z}'
    if min_voxel == max_voxel:
        function_file.write(f'setblock {min_set} {block}\n')
    else:
        max_x, max_y, max_z = max_voxel
        function_file.write(f'fill {min_set} ~{max_x - x} ~{max_y - y} ~{max_z - z} {block}\n')
