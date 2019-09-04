import csv
import click

from parseCsv import parseCsvToken, tokenToString

class UpdateElement():
    def __init__(self, fromToken, toToken):
        self.fromToken = fromToken
        self.toToken = toToken
        self.changed = False
    def updateElement(self, ele):
        if type(ele) == list:
            return tokenToString([self.updateElement(e) for e in ele])
        elif type(ele) == dict:
            return tokenToString({self.updateElement(key): self.updateElement(val) for key, val in ele.iteritems()})
        elif ele == self.fromToken:
            self.changed = True
            return self.toToken
        return ele

def replaceToken(fil, fromToken, toToken):
    updater = UpdateElement(fromToken, toToken)
    newRows = []
    with open(fil) as f:
        for row in csv.reader(f):
            newRows.append([updater.updateElement(parseCsvToken(ele)) for ele in row])
            
    if updater.changed:
        with open(fil, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(newRows)

@click.command()
@click.argument('fil')
@click.argument('fromtoken')
@click.argument('totoken')
def replaceTokenWrapper(fil, fromtoken, totoken):
    replaceToken(fil, fromtoken, totoken)

if __name__ == '__main__':
    replaceTokenWrapper()
