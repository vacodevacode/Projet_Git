# commands/cat_file.py

import sys
import os
import zlib

def run(args):
    if len(args) != 2 or args[0] != "-p":
        print("usage: mygit cat-file -p <sha1>")
        sys.exit(1)

    sha1 = args[1]
    path = f".git/objects/{sha1[:2]}/{sha1[2:]}"

    if not os.path.exists(path):
        print(f"fatal: object {sha1} not found")
        sys.exit(1)

    with open(path, 'rb') as f:
        compressed = f.read()

    decompressed = zlib.decompress(compressed)

    null_index = decompressed.find(b'\x00')
    content = decompressed[null_index + 1:]

    print(content.decode(), end='')
