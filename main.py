import argparse
import os
import fnmatch
import hashlib

class MyFile:
    partHashSize = 0
    def __init__(self, name):
        self.name = name
        self.size = os.path.getsize(self.name)
        self.processed = False
        self._partHash = None
        self._fullHash = None

    def __str__(self):
        return '{} is {}'.format(self.name, self.size)
    def __repr__(self):
        return '<MyFile {}:{}>'.format(self.name, self.size)

    def _getPartHash(self):
        if self._partHash is None:
            h = hashlib.sha1()
            with open(self.name, 'rb') as f:
                h.update(f.read(MyFile.partHashSize))
            self._partHash = h.hexdigest()
        return self._partHash
    partHash = property(_getPartHash)

    def _getFullHash(self):
        if self._fullHash is None:
            h = hashlib.sha256()
            with open(self.name, 'rb') as f:
                while True:
                    buf = f.read(MyFile.partHashSize)
                    if not buf:
                        break
                    h.update(buf)
                self._fullHash = h.hexdigest()
        return self._fullHash
    fullHash = property(_getFullHash)

        

def sizeParse(szstr):
    suffix = ['GB', 'MB', 'KB', 'B']
    for i, s in enumerate(suffix):
        if szstr.endswith(s):
            return int(szstr[0: len(szstr) - len(s)]) * (1024 ** (len(suffix) - i - 1))
    return int(szstr)

def recursiveDir(dir, pattern, filter):
    l = list()
    for root, dirs, files in os.walk(dir):
        for file in files:
            if fnmatch.fnmatch(file, pattern):
                f = MyFile(os.path.join(root, file))
                if filter(f):   
                    l.append(f)
    return l


def getFiles(arg, filter):
    if os.path.isfile(arg):
        return [MyFile(arg)]
    if os.path.isdir(arg):
        return recursiveDir(arg, '*', filter)
    [path, file] = os.path.split(arg)
    if len(path) == 0:
        path = '.'
    return recursiveDir(path, file, filter)

def main():
    parser = argparse.ArgumentParser(description='Duplicate File Finder')
    parser.add_argument('--min-size', dest= 'minsize', default='1KB', help='minimum file size, supports suffixes GB, MB, KB, B')
    parser.add_argument('--max-size', dest= 'maxsize', default='1024GB', help='maximum file size, supports suffixes GB, MB, KB, B')
    parser.add_argument('--hash-size', dest= 'hashsize', default='64KB', help='file hash size used for preliminary checking')
    parser.add_argument('dirs', metavar='dirs', type=str,
                        nargs='*', help='dirs or globs or files, supports glob patterns')
    args = parser.parse_args()
    MyFile.partHashSize = sizeParse(args.hashsize)
    MinimumSize = sizeParse(args.minsize)
    MaximumSize = sizeParse(args.maxsize)

    Files = list()
    [Files.extend(getFiles(x, lambda x: x.size > MinimumSize and x.size < MaximumSize)) for x in args.dirs]
    print(Files)

if __name__ == '__main__':
    main()




