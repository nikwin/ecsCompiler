import csv
import os

import click

@click.command()
@click.argument('foldername')
@click.argument('columns', nargs=-1)
@click.option('--flatten', is_flag=True, default=False)
def listRows(foldername, columns, flatten):
    files = os.listdir(foldername)
    pairs = []
    
    for fil in files:
        ext = os.path.splitext(fil)[1]
        if ext != '.csv':
            continue
                    
        with open(os.path.join(foldername, fil)) as f:
            columnNumbers = False
            for i, row in enumerate(csv.reader(f)):
                if not row: 
                    continue
                if i == 0:
                    columnNumbers = [row.index(column) for column in columns if column in row]
                    if not columnNumbers:
                        break
                    columnNumbers = [0] + columnNumbers
                else:
                    pairs.append([row[columnNumber] for columnNumber in columnNumbers if row[columnNumber]])
            
    if flatten:
        elements = []
        for pair in pairs:
            for ele in pair[1:]:
                elements.append(ele)
        print ' '.join(elements)
    else:
        for pair in pairs:
            print ','.join(pair)

if __name__ == '__main__':
    listRows()
