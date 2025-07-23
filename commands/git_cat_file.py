import sys
import os
import zlib

def run(args):
    if len(args) != 2 or args[0] not in ("-p", "-t"):
        print("usage: mygit cat-file -p|-t <sha1>")
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
    header = decompressed[:null_index]
    content = decompressed[null_index + 1:]

    if args[0] == "-p":
        print(content.decode(), end='')
    elif args[0] == "-t":
        type_str = header.decode().split()[0]
        print(type_str)

