import click
import csv
import json
import pyparsing

from parseCsv import parseCsvToken
from compileBase import *

class ArgWrapperEcs(object):
    def __init__(self, template, arg):
        self.template = template
        self.arg = arg
    def makeFunction(self, ecsKey, baseIndent):
        definition = """function(args){{
    updateArgs(args, JSON.parse(JSON.stringify(allArgs.{0})));
    return ecs.{1}(args);
}}""".format(ecsKey, self.template)
        return indent(definition, baseIndent)
    def getArg(self):
        return self.arg


def addCsvFileToEcs(f, fil, rawEcs, csvIdentifiers):
    csvKeys = []
    for i, row in enumerate(csv.reader(f)):
        if i == 0:
            keys = row
        else:
            if not row:
                continue
            try:
                tokens = [parseCsvToken(token) for token in row]
            except pyparsing.ParseException as e:
                print('csv parse failure in ' + fil)
                raise e
            defaultArgs = {key: token for key, token in zip(keys, tokens) if token is not None}
            try:
                key = defaultArgs['key']
            except KeyError:
                raise EcsException('No key in ' + fil)
            
            template = fil.split('_')[0]
            
            if key in rawEcs:
                raise EcsException('Duplicate key ' + key)
            else:
                rawEcs[key] = ArgWrapperEcs(template, defaultArgs)
            csvKeys.append(key)
    csvIdentifiers[fil] = csvKeys

def compileCsv(templateFolder, subFolder, oFile, partition):
    csvIdentifiers = {}
    rawEcs = {}
    
    for fil, f in getFilesInEcsFolder('.gen_csv', subFolder, partition):
        addCsvFileToEcs(f, fil, rawEcs, csvIdentifiers)
    
    for fil, f in getFilesInEcsFolder('.csv', subFolder, partition):
        if not fil in csvIdentifiers:
            addCsvFileToEcs(f, fil, rawEcs, csvIdentifiers)

    allArgs = {key: raw.getArg() for key, raw in rawEcs.items()}

    ecsList = ',\n'.join('    {}: {}'.format(key, raw.makeFunction(key, '    ')) for key, raw in rawEcs.items())
    
    templatePath = 'partitionFileTemplate.js' if partition else 'csvFileTemplate.js'
    with open(os.path.join(templateFolder, templatePath)) as templateFile:
        template = templateFile.read()

    definition = template.format(ecsList = ecsList,
                                 allArgs = json.dumps(allArgs, indent=4),
                                 csvIdentifiers = json.dumps(csvIdentifiers, indent=4),
                                 subFolder = subFolder)

    with open(oFile, 'w') as op:
        op.write(definition)


@click.command()
@click.argument('templatefolder')
@click.argument('subfolder')
@click.argument('ofile')
@click.option('--partition', is_flag=True)
def compileCsvWrapper(templatefolder, subfolder, ofile, partition):
    compileCsv(templatefolder, subfolder, ofile, partition)

if __name__ == '__main__':
    compileCsvWrapper()
