import os
import numpy as np
import random

from . import dpath, resolve_symbols, namespace_dir


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
# Affine transforms defining all 6 possible rotations
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


def off_shoots(settings, position, direction, cross_section):
    """
    Randomly choose 4 directions and remove the same and opposite directions (this will also
    create variation in the number of shoots).
    """
    for new_direction in random.choices(range(len(DIRECTIONS)), k=4):
        if new_direction not in (direction, OPPOSITE_DIRECTIONS[direction]):
            # randomly select a somewhat smaller cross-section and yield that off-shoot
            # (and it's shoots).
            new_cross_section = random.randrange(max(0, cross_section - 3), cross_section + 1)
            yield from branches(settings, position, new_direction, new_cross_section)


def branches(settings, position, direction, cross_section, min_length=None):
    """
    For a given start `position`, `direction`,  and `cross_section` index yields a branch
    definition and any off-shoots from that branch.
    """
    # Calculate the branch's length..
    branch_min_length = min_length if min_length else dpath.get(settings, '/branch_min_length')
    length = branch_min_length + cross_section * dpath.get(settings, '/branch_length_factor') + (
        random.uniform(0, 1) * dpath.get(settings, '/branch_variation_factor')
    )
    # ..and end position.
    end_position = np.add(position, DIRECTIONS[direction].dot((0, 0, length, 1)))
    if end_position[2] >= dpath.get(settings, '/lowest_branch_end'):
        # yield the branch definition (if it's high up enough)
        yield (position, direction, length, cross_section)
        if cross_section > 0:
            # always create a smaller branch in the same direction
            yield from branches(settings, end_position, direction, cross_section - 1)
            if cross_section > 1:
                # create smaller branches in random directions
                yield from off_shoots(settings, end_position, direction, cross_section - 2)


def fill_point(x, y, z, _):
    """
    Returns a string defining a set of minecraft fill coordinates relative to the actor.
    In minecraft, the y axis denotes the vertical (non-intuitively).
    """
    return f'~{int(x)} ~{int(z)} ~{int(y)}'


def leaves_fill(leaves_sample, lower, upper):
    """Returns a fill command for a block of `leaves` - randomly OAK or BIRCH."""
    return f'fill {fill_point(*lower)} {fill_point(*upper)} {random.choice(leaves_sample)}\n'


def leaves_fills(leaves_sample, position, direction, length, cross_section):
    """
    A generator yielding the fills for a random clump of leaves for the smallest 2 branch sizes.
    """
    if cross_section < 2:
        end_position = np.add(position, DIRECTIONS[direction].dot((0, 0, length, 1)))
        for _ in range(5):
            lower = [value + random.randrange(-2, 3) for value in end_position]
            upper = [value + random.randrange(-2, 3) for value in end_position]
            yield leaves_fill(leaves_sample, lower, upper)


def branch_fills(log_blocks, position, direction, length, cross_section):
    """A generator yielding the fills for a branch"""

    def transfrom(x, y, z):
        """Rotate and position a voxel"""
        return np.add(position, DIRECTIONS[direction].dot(np.array((x, y, z, 1))))

    # convert each cross section rectangle to a block range and thence a fill
    for (lower_x, lower_y), (upper_x, upper_y) in CROSS_SECTIONS[cross_section]:
        fill_lower = fill_point(*transfrom(lower_x, lower_y, 0))
        fill_upper = fill_point(*transfrom(upper_x, upper_y, length - 1))
        yield f'fill {fill_lower} {fill_upper} {log_blocks[direction]}\n'
        # Caps the branch with leaves to hide any grain (most will be overwritten by smaller
        # branches).
        cap_voxel = transfrom(lower_x, lower_y, length)
        yield leaves_fill(log_blocks, cap_voxel, cap_voxel)


def generate(settings):
    """
    Script to create a set of minecraft functions that create Cloud (very big) Trees. A recursive
    algorithm is randomly seeded to create 10 functions to create different trees.
    """
    namespace = namespace_dir(settings)

    start_pos = dpath.get(settings, '/start_position')
    trunk_min = dpath.get(settings, '/trunk_min_length')
    log_blocks = [
        resolve_symbols(settings, block) for block in dpath.get(settings, '/log_blocks')
    ]
    leaves_sample = [
        resolve_symbols(settings, block) for block in dpath.get(settings, '/leaves_sample')
    ]

    # create 10 cloud tree functions
    for tree in range(10):
        file_name = os.path.join(namespace, f'{tree}.mcfunction')
        with open(file_name, 'w') as file:
            # generate the branches
            for branch in branches(settings, start_pos, 0, len(CROSS_SECTIONS) - 1, trunk_min):
                # generate the fills for a branch's leaves (before the branch so the branch
                # overwrites the leaves if there is a clash)
                for fill in leaves_fills(leaves_sample, *branch):
                    file.write(fill)
                # generate the fills for a branch
                for fill in branch_fills(log_blocks, *branch):
                    file.write(fill)
