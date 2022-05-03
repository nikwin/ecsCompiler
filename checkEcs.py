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
@click.argument('paramfil', type=click.File('r'))
def checkEcs(paramfil):
    params = json.loads(paramfil.read())

    allArgs = {}
    allEcs = []
    for fil in params['files']:
        with open(fil, 'r') as f:
            parseFil(f.readlines(), allArgs, allEcs)

    for key, arg in allArgs.items():
        for field in params['fields']:
            if field in arg:
                entities = arg[field]
                if type(entities) == dict:
                    entities = entities.keys()
                elif type(entities) == str:
                    entities = [entities]
                elif entities == 0:
                    entities = []
            
                for entity in entities:
                    if not entity in allEcs:
                        print('{} Missing {}'.format(key, entity))

if __name__ == '__main__':
    checkEcs()
