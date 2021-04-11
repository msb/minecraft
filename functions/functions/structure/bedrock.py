import os
import re
import numpy as np
import bedrock
from .. import group_blocks_into_fills, write_fill

# A list of 2D affine transform matrices for the rotations: 0, 90, 180, 270.
ROTATION_MATRICES = (
    np.array(((1, 0, 0), (0, 1, 0), (0, 0, 1))),
    np.array(((0, -1, 0), (1, 0, 0), (0, 0, 1))),
    np.array(((-1, 0, 0), (0, -1, 0), (0, 0, 1))),
    np.array(((0, 1, 0), (-1, 0, 0), (0, 0, 1))),
)

# Used to test for a block being air.
AIR = ('air', )

# An instruction to void all air in a structure
VOID_AIR_INSTRUCTION = 'void_air'

# A volume that contains a set of structure blocks that, in turn, define volumes containing
# structures and the namespaces they belong to.
WORLD_INDEX_VOLUME = ((-1, 0, -1), (1, 255, 1))


class Plan:
    """
    Represents a function plan that defines how a basic structure should be converted to a
    function. There can be many plans for a structure (wall signs in the structure) defining many
    functions.
    """
    def __init__(self, wall_sign_text='#0\n0'):
        """
        Accepts and parses wall sign text into a `Plan`. The text s/b a set of instructions
        delimited by comma or newline. The 1st instructions is the `name` and the 2nd is the
        `rotation`. Other instructions can be either a `VOID_AIR_INSTRUCTION` or a number of
        `transmutations` that each tranmute one type of block to another such as
        "glass>stained_glass 15". If the block has rotations, no data value should be provided
        Eg. "sandstone_stairs>oak_stairs".
        """
        parts = re.split('\n|,', wall_sign_text[1:])
        self.name = parts[0]
        self.rotation = int(parts[1])
        self.transmutations = {before: after for before, after in [
            transmutation.split('>') for transmutation in parts[2:]
            if transmutation and transmutation != VOID_AIR_INSTRUCTION
        ]}
        self.do_air = VOID_AIR_INSTRUCTION in parts[2:]

    def transmute(self, name):
        """
        As described in `__init__` the `name` block is transmuted to another block if it matched
        one of the define `transmutations`
        """
        # we use modulus because name can be an array of 1 if the block has no rotations
        rotated_name = name[self.rotation % len(name)]
        parts = rotated_name.split()
        if len(parts) == 2 and parts[0] in self.transmutations:
            # this is the rotation case
            return ' '.join((self.transmutations[parts[0]], parts[1]))
        elif rotated_name in self.transmutations:
            return self.transmutations[rotated_name]
        return rotated_name

    def rotate(self, voxel, origin):
        """
        Rotates `voxel` about `origin` in the horizontal plane by 90 degrees `rotation` times.
        """
        rotated = ROTATION_MATRICES[self.rotation].dot(
            (voxel[0] - origin[0], voxel[2] - origin[2], 0)
        )
        return (rotated[0] + origin[0], voxel[1], rotated[1] + origin[2])


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
        # if there aren't any properties then just return the name.
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


def structure_block_volume(structure_block):
    """
    Calculates and returns a world volume from a structure block's volume. The world volume
    returned in the form: ((x_lower, y_lower, z_lower), (x_upper, y_upper, z_upper)).
    """
    block_volume_lower = (
        structure_block['x'] + structure_block['xStructureOffset'],
        structure_block['y'] + structure_block['yStructureOffset'],
        structure_block['z'] + structure_block['zStructureOffset'],
    )
    return (block_volume_lower, (
        block_volume_lower[0] + structure_block['xStructureSize'] - 1,
        block_volume_lower[1] + structure_block['yStructureSize'] - 1,
        block_volume_lower[2] + structure_block['zStructureSize'] - 1,
    ))


def volume_structure_blocks(world, volume_lower, volume_upper):
    """
    The generator that scans a volume in a world and yields only structure blocks.
    """
    for x, y, z in scan_volume(volume_lower, volume_upper):
        block = world.getBlock(x, y, z)
        if block and block.name == 'minecraft:structure_block':
            yield {
                **{tag.name: tag.payload for tag in block.nbt.payload},
                'x': x, 'y': y, 'z': z
            }


def scan_for_plans(world, structure_lower, structure_upper):
    """
    Searches a structure volume for wall signs with text beginning with "#". These are
    converting into function `Plan` objects and are returned in a map keyed with their
    position. At least one "identity" plan (named "0") is always returned so that at least
    one function is created.
    """
    # initialises the map with an identity plan.
    plans = {(0, -1, 0): Plan()}

    for x, y, z in scan_volume(structure_lower, structure_upper):
        block = world.getBlock(x, y, z)
        if block and 'minecraft:wall_sign' in block.name:
            sign = {
                tag.name: tag.payload for tag in block.nbt.payload
            }
            if sign['Text'] and sign['Text'].startswith('#'):
                if sign['Text'].startswith('#0,'):
                    # If an identity plan has been expicitly defined then remove the
                    # implicit one.
                    del plans[(0, -1, 0)]
                plans[(x, y, z)] = Plan(sign['Text'])
    return plans


def convert(path_to_save, path_to_functions, settings):
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

        def generate_volume(volume_lower, volume_upper, plans):
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
                    # ignore the block if either it's name is null or it's a plan
                    if not (name is None or (x, y, z) in plans):
                        yield (x - lower_x, y - lower_y, z - lower_z, name)

        def convert_structure_block(namespace, structure_block):
            """
            Converts the volume defined by a `structure_block` to a set of functions in a
            particular `namespace`. The number of functions depends on the number of function plans
            defined in the structure block's volume.
            """
            _, structure_name = structure_block['structureName'].split(':')
            print(structure_name)

            # read the block's volume
            block_volume_lower, block_volume_upper = structure_block_volume(structure_block)

            # scan a structure's volume for function plans
            plans = scan_for_plans(world, block_volume_lower, block_volume_upper)

            # convert the block's volume into a list of fills
            fills = group_blocks_into_fills(
                generate_volume(block_volume_lower, block_volume_upper, plans),
                [
                    upper_coord + 1 - lower_coord
                    for lower_coord, upper_coord in zip(block_volume_lower, block_volume_upper)
                ],
            )

            # order the fills, if an order has been defined
            if 'order_values' in settings:
                order_values = settings['order_values']
                # only sort by the name (not the data value)
                fills.sort(key=lambda f: order_values.get(f[2][0].split()[0], 50))

            # the origin is set so that the structure will be created as if you were standing in
            # the same position as the structure block.
            origin = (
                - structure_block['xStructureOffset'],
                - structure_block['yStructureOffset'],
                - structure_block['zStructureOffset'],
            )

            # write out a function for each plan
            for plan in plans.values():
                namespace_folder = os.path.join(path_to_functions, namespace)
                os.makedirs(namespace_folder, exist_ok=True)
                function_file = os.path.join(
                    namespace_folder, f'{structure_name}.{plan.name}.mcfunction'
                )
                with open(function_file, 'w') as file:
                    for min_voxel, max_voxel, name in fills:
                        if name != AIR or (name == AIR and plan.do_air):
                            write_fill(
                                file,
                                # rotate the structure according to the plan
                                plan.rotate(min_voxel, origin),
                                plan.rotate(max_voxel, origin),
                                # apply any transmutations according to the plan
                                plan.transmute(name),
                                origin
                            )

        # for each structure block in the `WORLD_INDEX_VOLUME` ..
        for index_block in volume_structure_blocks(world, *WORLD_INDEX_VOLUME):
            _, namespace = index_block['structureName'].split(':')
            index_block_volume = structure_block_volume(index_block)
            # .. and for each `structure_block` in the `index_block_volume` ..
            for structure_block in volume_structure_blocks(world, *index_block_volume):
                # .. convert that `structure_block` to a set of functions
                convert_structure_block(namespace, structure_block)
