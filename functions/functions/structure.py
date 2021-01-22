import os
import numpy as np
import bedrock
from nbt.nbt import NBTFile, TAG_List, TAG_Compound
from . import group_blocks_into_fills, write_fill

# A list of 2D affine transform matrices for the rotations: 0, 90, 180, 270.
ROTATION_MATRICES = (
    np.array(((1, 0, 0), (0, 1, 0), (0, 0, 1))),
    np.array(((0, -1, 0), (1, 0, 0), (0, 0, 1))),
    np.array(((-1, 0, 0), (0, -1, 0), (0, 0, 1))),
    np.array(((0, 1, 0), (-1, 0, 0), (0, 0, 1))),
)


def rotate_90(voxel, origin=(0, 0, 0), times=0):
    """
    Rotates `voxel` about `origin` in the horizontal plane by 90 degrees `times` times.
    """
    rotated = ROTATION_MATRICES[times].dot((voxel[0] - origin[0], voxel[2] - origin[2], 0))
    return (rotated[0] + origin[0], voxel[1], rotated[1] + origin[2])


def unpack_nbt(tag):
    """
    Unpack an NBT tag into a native Python data structure.
    """
    if isinstance(tag, TAG_List):
        return [unpack_nbt(i) for i in tag.tags]
    elif isinstance(tag, TAG_Compound):
        return {i.name: unpack_nbt(i) for i in tag.tags}
    else:
        return tag.value


def convert_java(nbt_file, function_file, settings):
    """
    Converts an NBT structure files into an mcfunction file.
    `block_name_map` map can be used to change block name
    (for example when creating a bedrock function).
    Blocks are grouped into fills where possible.
    """
    block_name_map = settings.get('block_name_map', {})
    strip_namespace = settings.get('strip_namespace')

    structure = unpack_nbt(NBTFile(nbt_file, 'rb'))

    # create a list of mapped blocks

    blocks = []

    for block in structure['blocks']:
        x, y, z = block['pos']
        block_data = structure['palette'][block['state']]
        name = block_data['Name']
        if strip_namespace:
            _, name = name.split(':')
        if 'Properties' in block_data:
            properties = [
                f'{key}={value}' for key, value in block_data['Properties'].items()
                # any properties with `false` values are assumed to be default and are ignored
                if value != 'false'
            ]
            name = f"{name}[{','.join(properties)}]"
        # change the block name if a map exists
        if name in block_name_map:
            name = block_name_map[name]
        if name is not None:
            blocks.append((x, y, z, name))

    # try to group contiguous blocks into fills
    fills = group_blocks_into_fills(blocks, structure['size'])

    if 'order_values' in settings:
        order_values = settings['order_values']
        fills.sort(key=lambda f: order_values.get(f[2], 50))

    # write out the function
    with open(function_file, 'w') as file:
        for min_voxel, max_voxel, name in fills:
            write_fill(file, min_voxel, max_voxel, name)


def scan_volume(volume_lower, volume_upper):
    """
    A generator that yields all the voxels for a volume.
    """
    lower_x, lower_y, lower_z = volume_lower
    upper_x, upper_y, upper_z = volume_upper

    for x in range(lower_x, upper_x + 1):
        for y in range(lower_y, upper_y + 1):
            for z in range(lower_z, upper_z + 1):
                yield (x, y, z)


def add_data_values(rotation_group_map, data_value_map_for_block, data_value_name, data_values):
    """
    For a block's given `data_value_name`, this function adds it's data value to the current
    `data_values`. If `data_value_name` has a rotation group, `data_values` is expanded to a list
    of 4 data values and the rotation group values are added to each item.
    """
    if data_value_name in rotation_group_map:
        rotation_group = rotation_group_map[data_value_name]
        # find the match `data_value_name` in the `rotation_group` and start from there.
        index = rotation_group.index(data_value_name)
        return [
            # it's safe to assume that `data_values` will be a list of one as there will only be
            # one rotation group per block type.
            data_values[0] + data_value_map_for_block[rotation_group[group_index % 4]]
            for group_index in range(index, index + 4)
        ]

    return [
        data_value + data_value_map_for_block[data_value_name]
        for data_value in data_values
    ]


def get_block_name(strip_namespace, data_value_map, rotation_group_map, block):
    """
    A function that converts a block's name and properties into a name and data value that can be
    used in a bedrock fill function. Returning a null data value indicates that the block shouldn't
    be set (useful for doors).
    """
    name = block.name

    if strip_namespace:
        _, name = name.split(':')

    if len(block.properties) == 0:
        # if there aren't any propertied then just return the name.
        return [name]

    data_value_map_for_block = data_value_map.get(name, {})

    # Initially a list of a single data value. If the block has different data values for different
    # rotations (eg. `facing_direction`) add_data_values() will change this into a list of four
    # values, one for each direction.
    data_values = [0]

    # Add the appropriate data values for each block properties.
    for prop in block.properties:
        data_value_name = f'{prop.name}:{prop.payload}'
        if data_value_name not in data_value_map_for_block:
            raise Exception(
                f'{name} requires a data value mapping of {data_value_name} but none is found.'
            )
        if data_value_map_for_block[data_value_name] is None:
            # a null data value indicates that the block shouldn't be set (useful for doors)
            data_values = None
            break
        data_values = add_data_values(
            rotation_group_map, data_value_map_for_block, data_value_name, data_values
        )

    if data_values is None:
        return None
    return [f'{name} {data_value}' for data_value in data_values]


def convert_bedrock(path_to_save, path_to_functions, settings):
    """
    Scans a volume in a bedrock world for structure blocks and converts the structures of any it
    finds to a set of bedrock functions.
    """
    with bedrock.World(path_to_save) as world:

        data_value_map = settings['data_value_map']
        strip_namespace = settings.get('strip_namespace')

        # create a map of the rotation group, keyed of the groups constituent data value names.
        rotation_group_map = {
            item: group for group in settings.get('rotation_groups', []) for item in group
        }

        def generate_volume(volume_lower, volume_upper):
            """
            A generator that yields all the blocks in a particular world's volume. The yielded
            blocks are tuples in a form accepted by group_blocks_into_fills().
            """
            lower_x, lower_y, lower_z = volume_lower

            for x, y, z in scan_volume(volume_lower, volume_upper):
                block = world.getBlock(x, y, z)
                if block is not None:
                    name = get_block_name(
                        strip_namespace, data_value_map, rotation_group_map, block
                    )
                    # a null can be returned, which means it should be ignored
                    if name is not None:
                        yield (x - lower_x, y - lower_y, z - lower_z, name)

        scan_volume_lower = settings['volume_lower']
        scan_volume_upper = settings['volume_upper']

        structure_blocks = []

        # scan the volume for structure block
        for x, y, z in scan_volume(scan_volume_lower, scan_volume_upper):
            block = world.getBlock(x, y, z)
            if block and block.name == 'minecraft:structure_block':
                structure_blocks.append({
                    **{tag.name: tag.payload for tag in block.nbt.payload},
                    'x': x, 'y': y, 'z': z
                })

        # for each structure block
        for structure_block in structure_blocks:
            _, structure_name = structure_block['structureName'].split(':')
            print(structure_name)

            # read the block's volume
            block_volume_lower = (
                structure_block['x'] + structure_block['xStructureOffset'],
                structure_block['y'] + structure_block['yStructureOffset'],
                structure_block['z'] + structure_block['zStructureOffset'],
            )
            block_volume_upper = (
                block_volume_lower[0] + structure_block['xStructureSize'] - 1,
                block_volume_lower[1] + structure_block['yStructureSize'] - 1,
                block_volume_lower[2] + structure_block['zStructureSize'] - 1,
            )
            # convert the block's volume into a list of fills
            fills = group_blocks_into_fills(
                generate_volume(block_volume_lower, block_volume_upper),
                [
                    upper_coord + 1 - lower_coord
                    for lower_coord, upper_coord in zip(block_volume_lower, block_volume_upper)
                ],
            )

            # order the fills, if an order has been defined
            if 'order_values' in settings:
                order_values = settings['order_values']
                fills.sort(key=lambda f: order_values.get(f[2][0], 50))

            # the origin is set so that the structure will be created as if you were standing in
            # the same position as the structure block.

            origin = (
                - structure_block['xStructureOffset'],
                - structure_block['yStructureOffset'],
                - structure_block['zStructureOffset'],
            )

            # write out a function for each 90 degree rotation.
            for rotation in range(4):
                function_file = os.path.join(
                    path_to_functions, f'{structure_name}.{rotation}.mcfunction'
                )
                with open(function_file, 'w') as file:
                    for min_voxel, max_voxel, name in fills:
                        write_fill(
                            file,
                            rotate_90(min_voxel, origin, rotation),
                            rotate_90(max_voxel, origin, rotation),
                            # we use modulus because name can be an array of 1 if the block has no
                            # rotations
                            name[rotation % len(name)],
                            origin
                        )
