import os
import numpy as np
import functools

# mincraft colour indicies
WHITE, ORANGE, MAGENTA, BLUE_LIGHT, \
    YELLOW, LIME, PINK, GREY, \
    GREY_LIGHT, CYAN, PURPLE, BLUE, \
    BROWN, GREEN, RED, BLACK = range(16)

# all blocks that the dome can be made of and their tag (to be used in the filename)
# (https://minecraft.gamepedia.com/Bedrock_Edition_data_values)
BLOCKS_AND_TAGS = (
    ('glass', 'clear'),
    (f'stained_glass {PINK}', 'pink'),
    (f'stained_glass {YELLOW}', 'yellow'),
    (f'stained_glass {BLUE_LIGHT}', 'blue')
)

# radiuses used to generate the domes
RADIUSES = (25, 32, 40)

# the namespace of the functions
NAMESPACE = 'dome'


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


def chunks(lst, n):
    """yield successive n-sized chunks from lst"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main():
    """
    Script to create a set of minecraft functions that builds domes, one for each combination of
    RADIUSES and BLOCKS_AND_TAGS.
    """
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
        for elevation in np.arange(-np.pi/24, np.pi/2, step)
    ]

    # make the namespace dir, if necessary
    namespace = os.path.join(os.getcwd(), NAMESPACE)
    os.makedirs(namespace, exist_ok=True)

    def create_dome_function(radius, block, tag):
        """
        Closure on `points` that creates a dome function from a block with a given radius.
        """

        # convert `points` to `voxels` and remove duplicates
        voxels = (np.array(points) * radius).astype(np.int16)
        uniqueVoxels = list({(x, y, z) for x, y, z in voxels})

        # minecraft functions can only execute 10000 commands, so we may have to split functions
        for i, chunk in enumerate(chunks(uniqueVoxels, 10000)):
            if i > 0:
                tag = f'{tag}_{i}'
            file_name = os.path.join(namespace, f'{radius}_{tag}.mcfunction')
            print(file_name)
            with open(file_name, 'w') as file:
                for x, y, z in chunk:
                    # in minecraft, the y axis is vertical (non-intuitively)
                    file.write(f'fill ~{x} ~{z} ~{y} ~{x} ~{z} ~{y} {block}\n')

    # create a dome function for each combination of RADIUSES and BLOCKS_AND_TAGS
    for radius in RADIUSES:
        for block, tag in BLOCKS_AND_TAGS:
            create_dome_function(radius, block, tag)


if __name__ == "__main__":
    main()
