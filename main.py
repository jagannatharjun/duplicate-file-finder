import argparse
import os
import fnmatch

class MyFile:
    def __init__(self, name):
        self.name = name
        self.size = os.path.getsize(self.name)
        

def sizeParse(szstr):
    suffix = ['GB', 'MB', 'KB', 'B']
    for i, s in enumerate(suffix):
        if szstr.endswith(s):
            return int(szstr[0: len(szstr) - len(s)]) * (1024 ** (len(suffix) - i - 1))
    return int(szstr)

def recursiveDir(dir, pattern):
    l = list()
    for root, dirs, files in os.walk(dir):
        for file in files:
            if fnmatch.fnmatch(file, pattern):
                l.append(os.path.join(root, file))
    return l


def getFiles(arg):
    if os.path.isfile(arg):
        return [arg]
    if os.path.isdir(arg):
        return recursiveDir(arg, '*')
    [path, file] = os.path.split(arg)
    if len(path) == 0:
        path = '.'
    return recursiveDir(path, file)

def main():
    parser = argparse.ArgumentParser(description='Duplicate File Finder')
    parser.add_argument('--min-size', dest= 'minsize', default='64KB', help='minimum file size, supports suffixes GB, MB, KB, B')
    parser.add_argument('--max-size', dest= 'maxsize', default='1024GB', help='maximum file size, supports suffixes GB, MB, KB, B')
    parser.add_argument('dirs', metavar='dirs', type=str,
                        nargs='*', help='dirs or globs or files, supports glob patterns')
    args = parser.parse_args()

    Files = list()
    [Files.extend(getFiles(x)) for x in args.dirs]
    MinimumSize = sizeParse(args.minsize)
    MaximumSize = sizeParse(args.maxsize)

if __name__ == '__main__':
    main()




