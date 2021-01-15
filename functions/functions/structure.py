import os
import bedrock
from nbt.nbt import NBTFile, TAG_List, TAG_Compound
from . import group_blocks_into_fills, write_fill


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


def get_block_name(strip_namespace, data_value_map, block):
    """
    A function that converts a block's name and properties into a name and data value that can be
    used in a bedrock fill function.
    """
    name = block.name

    if strip_namespace:
        _, name = name.split(':')

    if len(block.properties) == 0:
        # if there aren't any propertied then just return the name.
        return name

    data_value_map_for_block = data_value_map.get(name, {})
    data_value = 0
    for prop in block.properties:
        data_value_name = f'{prop.name}:{prop.payload}'
        if data_value_name not in data_value_map_for_block:
            raise Exception(
                f'{name} requires a data value mapping of {data_value_name} but none is found.'
            )
        # data values for different properties represent different bits and can be added.
        data_value += data_value_map_for_block[data_value_name]
    return f'{name} {data_value}'


def convert_bedrock(path_to_save, path_to_functions, settings):
    """
    Scans a volume in a bedrock world for structure blocks and converts the structures of any it
    finds to a set of bedrock functions.
    """
    with bedrock.World(path_to_save) as world:

        data_value_map = settings['data_value_map']
        strip_namespace = settings.get('strip_namespace')

        def generate_volume(volume_lower, volume_upper):
            """
            A generator that yields all the blocks in a particular world's volume. The yielded
            blocks are tuples in a form accepted by group_blocks_into_fills().
            """
            lower_x, lower_y, lower_z = volume_lower

            for x, y, z in scan_volume(volume_lower, volume_upper):
                block = world.getBlock(x, y, z)
                name = get_block_name(strip_namespace, data_value_map, block)
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
                fills.sort(key=lambda f: order_values.get(f[2], 50))

            # write out the function
            _, basename = structure_block['structureName'].split(':')
            function_file = os.path.join(path_to_functions, f'{basename}.mcfunction')
            with open(function_file, 'w') as file:
                for min_voxel, max_voxel, name in fills:
                    write_fill(file, min_voxel, max_voxel, name)
