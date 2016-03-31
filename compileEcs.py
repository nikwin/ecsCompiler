import os
import re
import json
import csv

from parseCsv import parseCsvToken
from parseToken import parseToken

def indent(definition, baseIndent):
    definition = definition.split('\n')
    for i in xrange(1, len(definition)):
        definition[i] = baseIndent + definition[i]
    definition = '\n'.join(definition)
    return definition

def defaultArgDefinition(key):
    return """updateArgs(args, JSON.parse(JSON.stringify(allArgs.{0})));""".format(key)

class Ecs(object):
    def __init__(self, ecs, inherits, commandHolders):
        self.ecs = ecs
        self.inherits = inherits
        self.commandHolders = commandHolders
    def reduce(self, rawEcs):
        ecs = {}
        commandHolders = {}
        for base in self.inherits:
            base = rawEcs[base]
            if len(base.inherits) > 0:
                return False
            for key, val in base.ecs.iteritems():
                ecs[key] = val
            for group, sdict in base.commandHolders.iteritems():
                if group not in commandHolders:
                    commandHolders[group] = {}
                for key, val in sdict.iteritems():
                    commandHolders[group][key] = val
        self.inherits = []

        for key, val in self.ecs.iteritems():
            ecs[key] = val

        if 'extend' in self.commandHolders:
            for key, val in self.commandHolders['extend'].iteritems():
                try:
                    ecs[key] = ecs[key] + '.concat(' + val + ')'
                except KeyError:
                    ecs[key] = val
        self.commandHolders['extend'] = {}
                
        for group, sdict in self.commandHolders.iteritems():
            if group not in commandHolders:
                commandHolders[group] = {}
            for key, val in sdict.iteritems():
                commandHolders[group][key] = val

        self.ecs = ecs
        self.commandHolders = commandHolders
        return True
    def makeFunction(self, ecsKey, baseIndent):
        ecsSet = ',\n'.join('{indent}{0}: {1}'.format(key, val, indent='        ') for key, val in self.ecs.iteritems())

        if 'refer' in self.commandHolders:
            if 'derive' not in self.commandHolders:
                self.commandHolders['derive'] = {}
            for key, val in self.commandHolders['refer'].iteritems():
                self.commandHolders['derive'][key] = 'allArgs[args["{0}"]].{1}'.format(val, key)

        if 'derive' in self.commandHolders:
            deriveText = ''.join('\n{indent}args["{0}"] = {1};'.format(key, val, indent='    ') for key, val in self.commandHolders['derive'].iteritems())
        else:
            deriveText = ''

        if 'default' in self.commandHolders:
            defaultText = ''.join('\n{indent}args["{0}"] = (args["{0}"] === undefined) ? {1} : args["{0}"];'.format(key, val, indent='    ') for key, val in self.commandHolders['default'].iteritems())
        else:
            defaultText = ''
        
        definition = """function(args){{{0}{1}{2}
    return {{
{ecsSet}
    }};
}}""".format(('\n    ' + defaultArgDefinition(ecsKey)) if self.getArg() else '', deriveText, defaultText, ecsSet=ecsSet)
        return indent(definition, baseIndent)
    def getArg(self):
        return self.commandHolders['arg'] if 'arg' in self.commandHolders else None
    def updateArgs(self, args):
        if not 'arg' in self.commandHolders:
            self.commandHolders['arg'] = args
        else:
            for key, val in args.iteritems():
                self.commandHolders['arg'][key] = val

class ArgWrapperEcs(object):
    def __init__(self, ref, arg):
        self.ref = ref
        self.arg = arg
    def makeFunction(self, ecsKey, baseIndent):
        definition = """function(args){{
    {0}
    return ecs.{1}(args);
}}""".format(defaultArgDefinition(ecsKey), self.ref)
        return indent(definition, baseIndent)
    def getArg(self):
        return self.arg

    
def getFilesInEcsFolder(ext):
    for folder, _, files in os.walk('ecs'):
        for fil in files:
            if os.path.splitext(fil)[1] == ext:
                with open(os.path.join(folder, fil)) as f:
                    yield os.path.splitext(fil)[0], f

def compileEcs(templateFolder):
    quotedLines = []
    rawEcs = {}
    for fil, f in getFilesInEcsFolder('.ecs'):
        shouldReset = True
        for lin in f.xreadlines():
            if shouldReset:
                ecs = {
                    'ecsKey': '"%s"'%(fil),
                    'args': 'args'
                }
                isQuoting = False
                inherits = []
                commandHolders = {}
                shouldReset = False
            
            if lin.strip() == '#':
                isQuoting = not isQuoting
                quotedLines.append('\n')
            elif isQuoting:
                quotedLines.append(lin)
            elif lin[:3] == '---':
                rawEcs[fil] = Ecs(ecs, inherits, commandHolders)
                fil = lin[3:].strip()
                shouldReset = True
            else:
                if not lin.strip():
                    continue
                mat = re.match('!(.+?) (.+)', lin)
                if mat:
                    group = mat.group(1)
                    if group == 'inherit':
                        inherits.append(mat.group(2))
                    else:
                        if group not in ['arg', 'derive', 'default', 'refer', 'extend']:
                            print 'incorrect instruction', fil
                        mat2 = re.match('(.+?) (.+)', mat.group(2))
                        key = mat2.group(1)
                        val = mat2.group(2)

                        if group == 'arg':
                            val = parseCsvToken(val)
                        elif group == 'extend':
                            val = parseToken(val, key).valToInsert()

                        if not group in commandHolders:
                            commandHolders[group] = {}
                        commandHolders[group][key] = val
                else:
                    try:
                        mat = re.match('(\w+): ?(.*)', lin)
                        key, val = mat.groups()
                    except AttributeError:
                        raise AttributeError(lin)
                    ecs[key] = parseToken(val, key).valToInsert()
                        
        rawEcs[fil] = Ecs(ecs, inherits, commandHolders)

    chk = False
    while not chk:
        chk = True
        for ecs in rawEcs.values():
            chk = ecs.reduce(rawEcs) and chk

    csvIdentifiers = {}
    for fil, f in getFilesInEcsFolder('.csv'):
        csvKeys = []
        for i, row in enumerate(csv.reader(f)):
            if i == 0:
                keys = row
            else:
                tokens = [parseCsvToken(token) for token in row]
                defaultArgs = { key: token for key, token in zip(keys, tokens) if token is not None }
                key = defaultArgs['key']
                template = defaultArgs['template'] if 'template' in defaultArgs else fil
                if key in rawEcs:
                    rawEcs[key].updateArgs(defaultArgs)
                else:
                    rawEcs[key] = ArgWrapperEcs(template, defaultArgs)
                csvKeys.append(key)
        csvIdentifiers[fil] = csvKeys

    parameters = rawEcs['PARAMETERS'].commandHolders['arg']
    del rawEcs['PARAMETERS']

    allArgs = { key: raw.getArg() for key, raw in rawEcs.iteritems() if raw.getArg() }
    allEcs = { key: raw.makeFunction(key, '    ') for key, raw in rawEcs.iteritems() }

    ecsList = ',\n'.join('    {0}: {1}'.format(key, val) for key, val in allEcs.iteritems())
    
                 
    with open(os.path.join(templateFolder, 'fileTemplate.js')) as templateFile:
        template = templateFile.read()

    ecsDefinition = template.format(parameters=json.dumps(parameters, indent=4),
           allArgs=json.dumps(allArgs, indent=4), 
           ecsList=ecsList, 
           quotedLines=''.join(quotedLines), 
           csvIdentifiers=json.dumps(csvIdentifiers, indent=4))
    print ecsDefinition


if __name__ == '__main__':
    import sys
    baseFolder = os.path.split(sys.argv[0])[0]
    compileEcs(os.path.join(baseFolder, 'templates'))
