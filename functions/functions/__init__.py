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
