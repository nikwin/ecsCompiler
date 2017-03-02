import os
import re
import csv

from parseCsv import parseCsvToken

import click

@click.command()
@click.argument('foldername')
@click.option('--pretty', is_flag=True)
def checkFolder(foldername, pretty):
    files = os.listdir(foldername)

    allKeys = set()
    foundKeys = set()

    def addToken(token):
        token = parseCsvToken(token)
        if type(token) == str:
            foundKeys.add(token)
        elif type(token) == dict:
            foundKeys.update(token.keys())
        elif type(token) == list:
            foundKeys.update(token)
                        
    keysForFil = {}


    for fil in files:
        ext = os.path.splitext(fil)[1]
        path = os.path.join(foldername, fil)
        
        if ext == '.ecs':
            with open(path) as f:
                for lin in f.xreadlines():
                    mat = re.match('!arg [^ ]+ (.*)', lin)
                    if mat:
                        addToken(mat.groups()[0])
            continue

        if ext == '.csv':
            if fil.replace('.csv', '.gen_csv') in files:
                continue
        elif ext != '.gen_csv':
            continue
        
        keysForFil[fil] = []

        with open(path) as f:
            for i, row in enumerate(csv.reader(f)):
                if i == 0:
                    continue
                for j, part in enumerate(row):
                    if j == 0:
                        keysForFil[fil].append(part)
                        allKeys.add(part)
                    else:
                        if ' ' not in part:
                            addToken(part)

    unusedKeys = allKeys.difference(foundKeys)
    missingKeys = foundKeys.difference(allKeys)

    missingKeysForFil = ((fil, [key for key in keys if key in unusedKeys]) for fil, keys in keysForFil.iteritems())
    missingKeysForFil = ((fil, keys) for fil, keys in missingKeysForFil if keys)
    
    missingKeysForFil = ((fil, keys) for fil, keys in missingKeysForFil if len(keysForFil[fil]) != len(keys))
    
    if pretty:
        for fil, keys in missingKeysForFil:
            print '%s - %d / %d'%(fil, len(keys), len(keysForFil[fil]))
            for key in keys:
                print '  ' + key
    else:
        keysToPrint = []
        for fil, keys in missingKeysForFil:
            keysToPrint += keys
        print ' '.join(keysToPrint)

    return unusedKeys, missingKeys

if __name__ == '__main__':
    checkFolder()
    
