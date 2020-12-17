import os

class EcsException(Exception):
    pass

def getFilesInEcsFolder(ext, subFolder, partition):
    if partition:
        walk = ((folder, files) for folder, _, files in os.walk(subFolder))
    else:
        walk = ((folder, files) for folder, _, files in os.walk('ecs') 
                   if folder == 'ecs' or os.path.normpath(folder) == os.path.normpath(subFolder))

    for folder, files in walk:
        for fil in files:
            if os.path.splitext(fil)[1] == ext:
                with open(os.path.join(folder, fil)) as f:
                    yield os.path.splitext(fil)[0], f

def indent(definition, baseIndent):
    definition = definition.split('\n')
    for i in range(1, len(definition)):
        definition[i] = baseIndent + definition[i]
    definition = '\n'.join(definition)
    return definition
