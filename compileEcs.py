import click
import os
import re
import json
import csv

import pyparsing

from parseCsv import parseCsvToken
from parseToken import parseToken, DirectEcsRef, DirectConditionEcs
from compileBase import *

class Ecs(object):
    def __init__(self, ecs, inherits, asserts, commandHolders, key):
        self.ecs = ecs
        self.inherits = inherits
        self.asserts = asserts
        self.commandHolders = commandHolders
        self.key = key
    def reduce(self, rawEcs):
        ecs = {}
        commandHolders = {}
        for base in self.inherits:
            try:
                base = rawEcs[base]
            except KeyError:
                raise EcsException('{} could not inherit from {}'.format(self.key, base))
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
        ecsSet = ',\n'.join('        {0}: {1}'.format(key, val) for key, val in self.ecs.iteritems())

        commandLines = []

        if 'refer' in self.commandHolders:
            if 'derive' not in self.commandHolders:
                self.commandHolders['derive'] = {}
            for key, val in self.commandHolders['refer'].iteritems():
                self.commandHolders['derive'][key] = 'allArgs[args["{0}"]].{1}'.format(val, key)

        if 'derive' in self.commandHolders:
            commandLines += ['args["{0}"] = {1};'.format(key, val) for key, val in self.commandHolders['derive'].iteritems()]

        if 'default' in self.commandHolders:
            commandLines += ['args["{0}"] = (args["{0}"] === undefined) ? {1} : args["{0}"];'.format(key, val) for key, val in self.commandHolders['default'].iteritems()]
            

        commandLines += ['if (args.{0} === undefined){{ throw "ECS fail " + args.key + " missing {0}"; }}'.format(val) for val in self.asserts]
        
        commandLines = '\n'.join('    ' + line for line in commandLines)
        
        definition = """function(args){{
    if (allArgs.{ecsKey}){{
        updateArgs(args, JSON.parse(JSON.stringify(allArgs.{ecsKey})));
    }}
{commandLines}
    return {{
{ecsSet}
    }};
}}""".format(ecsKey=ecsKey, commandLines=commandLines, ecsSet=ecsSet)
        return indent(definition, baseIndent)

def argToDefine(val):
    if type(val) == str:
        return '"{}"'.format(val)
    else:
        return val

def compileEcs(templateFolder, subFolder, oFile):
    quotedLines = []
    rawEcs = {}

    baseEcs = []
    with open(os.path.join(templateFolder, 'ecsTemplate')) as ecsTemplateFil:
        for lin in ecsTemplateFil.xreadlines():
            baseEcs.append([e.strip() for e in lin.split(':')])
            

    for fil, f in getFilesInEcsFolder('.ecs', subFolder):
        baseFil = fil
        shouldReset = True
        fileEcs = None
        for lin in f.xreadlines():
            if shouldReset:
                ecs = {key: val.format(fil=fil) for key, val in baseEcs}
                isQuoting = False
                inherits = []
                asserts = []
                commandHolders = {}
                shouldReset = False
                inFunction = False
            
            if lin.strip() == '#':
                isQuoting = not isQuoting
                quotedLines.append('\n')
            elif isQuoting:
                quotedLines.append(lin)
            elif inFunction:
                quotedLines.append(lin)
                inFunction = lin != '};\n'
            elif lin[:3] == '---':
                rawEcs[fil] = Ecs(ecs, inherits, asserts, commandHolders, fil)

                if not fileEcs:
                    fileEcs = rawEcs[fil]

                fil = lin[3:].strip()
                
                fil = fil.split(' ')
                commands = fil[1:]
                fil = fil[0]
                key = fil

                if fil == '~':
                    fil = baseFil + 'Component'
                    key = fil
                elif '~' in fil:
                    key = fil[1:]
                    fil = baseFil + fil[1].upper() + fil[2:]
                
                if key not in fileEcs.ecs and not '!noset' in commands:
                    condition = next((command for command in commands if command[0] == '?'), None)
                    if condition:
                        condition = condition[1:]
                        ecsRef = DirectConditionEcs(condition, fil)
                    else:
                        ecsRef = DirectEcsRef(fil)
                    fileEcs.ecs[key] = ecsRef.valToInsert()

                shouldReset = True
            else:
                if not lin.strip():
                    continue
                mat = re.match('!(.+?) (.+)', lin)
                if mat:
                    group = mat.group(1)
                    if group == 'inherit':
                        inherits.append(mat.group(2))
                    elif group == 'assert':
                        asserts.append(mat.group(2))
                    else:
                        if group not in ['arg', 'derive', 'default', 'refer', 'extend']:
                            print 'incorrect instruction in', fil, '-', group
                        mat2 = re.match('(.+?) (.+)', mat.group(2))
                        try:
                            key = mat2.group(1)
                            val = mat2.group(2)
                        except AttributeError:
                            raise AttributeError(lin)

                        if group == 'arg':
                            val = parseCsvToken(val)
                            val = argToDefine(val)
                            
                            group = 'derive'
                        elif group == 'extend':
                            val = parseToken(val, key, fil).valToInsert()

                        if not group in commandHolders:
                            commandHolders[group] = {}
                        commandHolders[group][key] = val
                else:
                    if lin[0] == '~':
                        key, val = lin.split(':')
                        key = key.strip()
                        val = val.strip()
                        
                        if key == '~':
                            key = baseFil + 'Component'
                        else:
                            key = baseFil + key[1].upper() + key[2:]
                    else:
                        try:
                            mat = re.match('(\w+): ?(.*)', lin)
                            key, val = mat.groups()
                        except AttributeError:
                            raise AttributeError(lin)

                    if 'function' in val:
                        inFunction = True
                        
                        fnName = fil + '_' + key
                        ecs[key] = fnName
                        quotedLines.append('var {} = {}\n'.format(fnName, val))
                        
                    else:
                        parsed = parseToken(val, key, fil)
                        try:
                            ecs[key] = parsed.valToInsert()
                        except TypeError as e:
                            print 'Error parsing - ', lin
                            raise e
                        
                        try:
                            newAssert = parsed.getAsserts()
                            asserts.append(newAssert)
                        except AttributeError:
                            pass
                    
                        
        rawEcs[fil] = Ecs(ecs, inherits, asserts, commandHolders, fil)

    chk = False
    while not chk:
        chk = True
        for ecs in rawEcs.values():
            chk = ecs.reduce(rawEcs) and chk

    parameters = rawEcs['PARAMETERS'].commandHolders['derive']
    del rawEcs['PARAMETERS']
    
    parameters = ',\n'.join('   {}: {}'.format(key, val) for key, val in parameters.iteritems())

    allEcs = { key: raw.makeFunction(key, '    ') for key, raw in rawEcs.iteritems() }
    ecsList = ',\n'.join('    {0}: {1}'.format(key, val) for key, val in allEcs.iteritems())
    
                 
    with open(os.path.join(templateFolder, 'fileTemplate.js')) as templateFile:
        template = templateFile.read()

    ecsDefinition = template.format(parameters=parameters,
                                    ecsList=ecsList, 
                                    quotedLines=''.join(quotedLines))

    with open(oFile, 'w') as op:
        op.write(ecsDefinition)

@click.command()
@click.argument('templatefolder')
@click.argument('subfolder')
@click.argument('ofile')
def compileEcsWrapper(templatefolder, subfolder, ofile):
    compileEcs(templatefolder, subfolder, ofile)

if __name__ == '__main__':
    compileEcsWrapper()
