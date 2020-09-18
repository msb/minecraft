from nbt.nbt import NBTFile, TAG_Long, TAG_Int, TAG_String, TAG_List, TAG_Compound


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


def generate(nbt_file, function_file):
    """
    Converts an NBT structure files into an mcfunction file.
    """
    structure = unpack_nbt(NBTFile(nbt_file,'rb'))
    print(structure)
    with open(function_file, 'w') as file:
        for block in structure['blocks']:
            x, z, y = block['pos']
            block_data = structure['palette'][block['state']]
            name = block_data['Name']
            if 'Properties' in block_data:
                properties = [f'{key}={value}'for key, value in block_data['Properties'].items()]
                name = f"{name}[{','.join(properties)}]"
            file.write(f'setblock ~{x} ~{z} ~{y} {name}\n') # FIXME remove fudge
