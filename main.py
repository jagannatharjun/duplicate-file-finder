import argparse

parser = argparse.ArgumentParser(description='Duplicate File Finder')
parser.add_argument('Dirs', metavar='dirs', type=str,
                    nargs='*', help='dirs or globs, supports glob patterns')
