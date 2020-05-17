import os
import numpy as np
import random


def rotate_90(rectangle):
    """Rotates a rectangle (2x2 coordinates) by 90"""
    return [(-y, x) for x, y in rectangle]


def add_a_half(rectangle):
    """Adds 0.5 to a rectangle (2x2 coordinates)"""
    return [(x + 0.5, y + 0.5) for x, y in rectangle]


def generate_cross_section(partial_cross_section):
    """
    Converts the partial branch cross sections into complete cross sections by rotating each
    rectangle 3 time. The partial cross sections use 0.5 values so the rotation works - then 0.5 is
    adds so we can use integers.
    """
    cross_section = []
    for rectangle in partial_cross_section:
        cross_section.insert(0, rectangle)
        for _ in range(3):
            cross_section.insert(0, rotate_90(cross_section[0]))
    return [add_a_half(rectangle) for rectangle in cross_section]


# A set of branch cross sections (built from rectangles), increasing in size. They are partial
# because only one quadrant of the cross section is defined.
PARTIAL_CROSS_SECTIONS = (
    (((0.5,  0.5), (0.5, 0.5)),),
    (((-0.5,  1.5), (0.5, 1.5)),),
    (((-0.5,  1.5), (1.5, 1.5)),),
    (((2.5, -0.5), (2.5, 0.5)), ((1.5, 1.5), (1.5, 1.5))),
    (((3.5, -0.5), (3.5, 0.5)), ((1.5, 2.5), (1.5, 2.5)), ((2.5,  1.5), (2.5, 1.5))),
    (((3.5, -1.5), (3.5, 1.5)), ((2.5, 2.5), (2.5, 2.5))),
    (((3.5, -2.5), (3.5, 2.5)),),
    (((2.5,  3.5), (2.5, 3.5)), ((3.5, 2.5), (3.5, 2.5)), ((4.5, -1.5), (4.5, 1.5))),
)

# The smallest cross section is a single block.
TOP_CROSS_SECTION = (((0, 0), (0, 0)),)

# A set of branch cross sections (built from rectangles), increasing in size.
CROSS_SECTIONS = [TOP_CROSS_SECTION] + [
    generate_cross_section(cross_section) for cross_section in PARTIAL_CROSS_SECTIONS
]


# the namespace of the functions
NAMESPACE = 'cloudtree'

# `log` data values defining wood type and direction
# (https://minecraft.gamepedia.com/Bedrock_Edition_data_values)
OAK_UD, SPRUCE_UD, BIRCH_UD, JUNGLE_UD, \
    OAK_EW, SPRUCE_EW, BIRCH_EW, JUNGLE_EW, \
    OAK_NS, SPRUCE_NS, BIRCH_NS, JUNGLE_NS = range(12)

# `leaves` data values defining leaf type
# (https://minecraft.gamepedia.com/Bedrock_Edition_data_values)
OAK_LEAVES, SPRUCE_LEAVES, BIRCH_LEAVES, JUNGLE_LEAVES, \
    X_4, X_5, X_6, X_7, \
    OAK_LEAVES_2, SPRUCE_LEAVES_2, BIRCH_LEAVES_2, JUNGLE_LEAVES_2 = range(12)

# These are constants controlling aspects the branch's length:
# No branch is less that this
BRANCH_MIN_LENGTH = 8
# Multiplies cross section index then added to length
BRANCH_LENGTH_FACTOR = 0.4
# Controls size of a random constant added to length
BRANCH_VARIATION_FACTOR = 4

# A branch cannot extend down passed this z value (relative to actor)
LOWEST_BRANCH_END = 10
# Where the trunk is placed relative to actor (the 1 is for the affine tranforms)
START_POSITION = (0, 0, -2, 1)
# This overrides BRANCH_MIN_LENGTH for the trunk
TRUNK_MIN_LENGTH = 30

# Affine transforms defining all 6 possible
DIRECTIONS = (
    np.array(((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))),
    np.array(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1))),
    np.array(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1))),
    np.array(((0, 0, 1, 0), (0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 0, 1))),
    np.array(((0, 0, -1, 0), (0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 1))),
    np.array(((-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, -1, 0), (0, 0, 0, 1))),
)
# For each DIRECTION, gives the opposite direction
OPPOSITE_DIRECTIONS = (5, 2, 1, 4, 3, 0)
# The `log` tile data ordered to match DIRECTIONS
TILE_DATA = (OAK_UD, OAK_NS, OAK_NS, OAK_EW, OAK_EW, OAK_UD)


def off_shoots(position, direction, cross_section):
    """FIXME"""
    # Randomly choose 4 directions and remove the same and opposite directions (this will also
    # create variation in the number of shoots).
    for new_direction in random.choices(range(len(DIRECTIONS)), k=4):
        if new_direction not in (direction, OPPOSITE_DIRECTIONS[direction]):
            # randomly select a somewhat smaller cross-section and yield that off-shoot
            # (and it's shoots).
            new_cross_section = random.randrange(max(0, cross_section - 3), cross_section + 1)
            yield from branches(position, new_direction, new_cross_section)


def branches(position, direction, cross_section, branch_min_length=BRANCH_MIN_LENGTH):
    """
    For a given start `position`, `direction`,  and `cross_section` index yields a branch
    definition and any off-shoots from that branch.
    """
    # Calculate the branch's length..
    length = branch_min_length + cross_section * BRANCH_LENGTH_FACTOR + (
        random.uniform(0, 1) * BRANCH_VARIATION_FACTOR
    )
    # ..and end position.
    end_position = np.add(position, DIRECTIONS[direction].dot((0, 0, length, 1)))
    if end_position[2] >= LOWEST_BRANCH_END:
        # yield the branch definition (if it's high up enough)
        yield (position, direction, length, cross_section)
        if cross_section > 0:
            # always create a smaller branch in the same direction
            yield from branches(end_position, direction, cross_section - 1)
            if cross_section > 1:
                # create smaller branches in random directions
                yield from off_shoots(end_position, direction, cross_section - 2)


def fill_point(x, y, z, _):
    """
    Returns a string defining a set of minecraft fill coordinates relative to the actor.
    In minecraft, the y axis denotes the vertical (non-intuitively).
    """
    return f'~{int(x)} ~{int(z)} ~{int(y)}'


def leaves_fill(lower, upper):
    """Returns a fill command for a block of `leaves` - randomly OAK or BIRCH."""
    leaves = random.choice((OAK_LEAVES, BIRCH_LEAVES))
    return f'fill {fill_point(*lower)} {fill_point(*upper)} leaves {leaves}\n'


def leaves_fills(position, direction, length, cross_section):
    """
    A generator yielding the fills for a random clump of leaves for the smallest 2 branch sizes.
    """
    if cross_section < 2:
        end_position = np.add(position, DIRECTIONS[direction].dot((0, 0, length, 1)))
        for _ in range(5):
            lower = [value + random.randrange(-2, 3) for value in end_position]
            upper = [value + random.randrange(-2, 3) for value in end_position]
            yield leaves_fill(lower, upper)


def branch_fills(position, direction, length, cross_section):
    """A generator yielding the fills for a branch"""

    def transfrom(x, y, z):
        """Rotate and position a voxel"""
        return np.add(position, DIRECTIONS[direction].dot(np.array((x, y, z, 1))))

    # convert each cross section rectangle to a block range and thence a fill
    for (lower_x, lower_y), (upper_x, upper_y) in CROSS_SECTIONS[cross_section]:
        block = TILE_DATA[direction]
        lower_voxel = transfrom(lower_x, lower_y, 0)
        upper_voxel = transfrom(upper_x, upper_y, length - 1)
        yield f'fill {fill_point(*lower_voxel)} {fill_point(*upper_voxel)} log {block}\n'
        # Caps the branch with leaves to hide any grain (most will be overwritten by smaller
        # branches).
        cap_voxel = transfrom(lower_x, lower_y, length)
        yield leaves_fill(cap_voxel, cap_voxel)


def main():
    """
    Script to create a set of minecraft functions that create Cloud (very big) Trees. A recursive
    algorithm is randomly seeded to create 10 functions to create different trees.
    """
    # make the namespace dir, if necessary
    namespace = os.path.join(os.getcwd(), NAMESPACE)
    os.makedirs(namespace, exist_ok=True)

    # create 10 cloud tree functions
    for tree in range(10):
        file_name = os.path.join(namespace, f'{tree}.mcfunction')
        with open(file_name, 'w') as file:
            # generate the branches
            for branch in branches(START_POSITION, 0, len(CROSS_SECTIONS) - 1, TRUNK_MIN_LENGTH):
                # generate the fills for a branch's leaves (before the branch so the branch
                # overwrites the leaves if there is a clash)
                for fill in leaves_fills(*branch):
                    file.write(fill)
                # generate the fills for a branch
                for fill in branch_fills(*branch):
                    file.write(fill)


if __name__ == "__main__":
    main()
