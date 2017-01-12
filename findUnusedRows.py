import os
import re
import sys
import csv

from parseCsv import parseCsvToken

def checkFolder(foldername):
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
        
        with open(path) as f:
            for i, row in enumerate(csv.reader(f)):
                if i == 0:
                    continue
                for j, part in enumerate(row):
                    if j == 0:
                        allKeys.add(part)
                    else:
                        if ' ' not in part:
                            addToken(part)

    unusedKeys = allKeys.difference(foundKeys)
    missingKeys = foundKeys.difference(allKeys)
    return unusedKeys, missingKeys

if __name__ == '__main__':
    folder = sys.argv[1]
    unusedKeys, missingKeys = checkFolder(folder)
    print 'Unused Keys:'
    for key in unusedKeys:
        print key
