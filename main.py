import argparse
import os
import fnmatch
import hashlib
import time

class MyFile:
    partHashSize = 0
    def __init__(self, name):
        self.name = name
        self.size = os.path.getsize(self.name)
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

    def findDuplicates(self, files):
        if self._processed:
            return list()
        dup = list()
        for f in files:
            if f.size == self.size and not os.path.samefile(f.name, self.name):
                if f.partHash == self.partHash and f.fullHash == self.fullHash:
                    f._processed = True
                    dup.append(f)
        if len(dup) > 0:
            dup.append(self)
        return dup                           

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

def classify(seq, key):
    buckets = {}
    for item in seq:
        k = key(item)
        if not k in buckets:
            buckets[k] = [item]
        else:
            buckets[k].append(item)
    
    return buckets

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

    files = []
    for d in args.dirs:
        print("searching", d)
        files.extend(getFiles(d, lambda x: x.size > MinimumSize and x.size < MaximumSize))

    dupSize = 0
    sameSizeFiles = classify(files, lambda f : f.size)
    for size, files in sameSizeFiles.items():
        if len(files) <= 1:
            continue

        samePartHash = classify(files, lambda f : f.partHash)
        for partHash, files in samePartHash.items():
            if len(files) > 1:
                sameFiles = classify(files, lambda f : f.fullHash)
                for fullHash, files in sameFiles.items():
                    print(fullHash, files)
                    for file in files:
                        dupSize += file.size


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print("took", end - start)
