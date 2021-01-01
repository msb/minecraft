import os
from . import dpath, resolve_symbols, namespace_dir


def generate(settings):
    """
    Generates functions to create a maze.
    """
    name = dpath.get(settings, '/name')
    namespace = namespace_dir(settings)

    # if `tiles` is defined we create each of the tile functions
    # (otherwise we assume they are created by other means)
    tiles = dpath.get(settings, '/tiles', default=None)
    if tiles:
        edges = dpath.get(settings, '/edges')
        for tile_name, edge_indices in tiles:
            with open(os.path.join(namespace, f'{name}.{tile_name}.mcfunction'), 'w') as file:
                # we always render all corners
                for corner in dpath.get(settings, '/corners'):
                    file.write(resolve_symbols(settings, corner) + '\n')
                # we only render edges defined by `edge_indices`
                for edge_index in edge_indices:
                    file.write(resolve_symbols(settings, edges[edge_index]) + '\n')

    # create the main function which positions each of the tiles defined in `maze`
    with open(os.path.join(namespace, f'{name}.mcfunction'), 'w') as file:
        x_spacing, z_spacing = dpath.get(settings, '/tile_spacing')
        for z, row in enumerate(dpath.get(settings, '/maze')):
            for x, tile in enumerate(row):
                command = f'function maze:{name}.{tile}'
                file.write(
                  f'execute positioned ~{x * x_spacing} ~ ~{z * z_spacing} run {command}\n'
                )
