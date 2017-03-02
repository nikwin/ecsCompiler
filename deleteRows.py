import os
import csv

def deleteKeys(folder, keys):
    for fil in os.listdir(folder):
        if os.path.splitext(fil)[1] == '.csv':
            with open(os.path.join(folder, fil)) as f:
                rows = [row for row in csv.reader(f)]
                origLength = len(rows)
                rows = [row for row in rows if not row or row[0] not in keys]
                
            if origLength == len(rows):
                continue

            with open(os.path.join(folder, fil), 'w') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
    print ' '.join(keys)

if __name__ == '__main__':
    import sys
    folder = sys.argv[1]
    keys = sys.argv[2:]
    deleteKeys(folder, keys)
