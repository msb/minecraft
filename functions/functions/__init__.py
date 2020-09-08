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
