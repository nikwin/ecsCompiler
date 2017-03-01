import csv
import os

def listRows(folder, column):
    files = os.listdir(folder)
    pairs = []
    
    for fil in files:
        ext = os.path.splitext(fil)[1]
        if ext != '.csv':
            continue
                    
        with open(os.path.join(folder, fil)) as f:
            columnNumber = -1
            try:
                for i, row in enumerate(csv.reader(f)):
                    if not row: 
                        continue
                    if i == 0:
                        columnNumber = row.index(column)
                    else:
                        pairs.append((row[0], row[columnNumber]))
            except ValueError:
                pass

    longestKey = max(len(pair[0]) for pair in pairs)
    for pair in pairs:
        print ','.join(pair)

if __name__ == '__main__':
    import sys
    folder = sys.argv[1]
    column = sys.argv[2]
    listRows(folder, column)
