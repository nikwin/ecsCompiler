import click
import json
import re

def parseFil(lines, allArgs, allEcs):
    currentArgs = False
    ecsMode = False
    for lin in lines:
        if re.match(r'var .*allArgs = \{', lin):
            currentArgs = '{'
        elif re.match(r'var .*[Ee]cs = \{', lin):
            ecsMode = True
        elif lin.startswith('};'):
            if currentArgs:
                currentArgs += '}'
                allArgs.update(json.loads(currentArgs))
            currentArgs = False
            ecsMode = False
        elif ecsMode:
            mat = re.match(r'\s*(\w+): function\(args\)\{', lin)
            if mat:
                allEcs.append(mat.group(1))
        elif currentArgs:
            currentArgs += lin

@click.command()
@click.argument('fils', type=click.File('r'), nargs=-1)
def checkEcs(fils):
    allArgs = {}
    allEcs = []
    for fil in fils:
        parseFil(fil.readlines(), allArgs, allEcs)

    for key, arg in allArgs.items():
        if 'entitiesToMake' in arg:
            entities = arg['entitiesToMake']
            if type(entities) == dict:
                entities = entities.keys()
            elif type(entities) == str:
                entities = [entities]
            
            for entity in entities:
                if not entity in allEcs:
                    print('{} Missing {}'.format(key, entity))

if __name__ == '__main__':
    checkEcs()
