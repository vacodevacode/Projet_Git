import sys
import os
import hashlib
import zlib

def git_hash_object(filepath, write=False):
    if not os.path.exists(filepath):
        print(f"fatal: path '{filepath}' does not exist")
        sys.exit(1)
    if os.path.isdir(filepath):
        print(f"fatal: {filepath} is a directory")
        sys.exit(1)

    with open(filepath, 'rb') as f:
        content = f.read()

    header = f"blob {len(content)}\0".encode()
    full_data = header + content
    sha1 = hashlib.sha1(full_data).hexdigest()
    print(sha1)

    if write:
        path = f".git/objects/{sha1[:2]}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/{sha1[2:]}", 'wb') as f:
            f.write(zlib.compress(full_data))

def run(args):
    if not args:
        print("usage: mygit hash-object [-w] <file>")
        sys.exit(1)

    if args[0] == "-w":
        if len(args) != 2:
            print("usage: mygit hash-object [-w] <file>")
            sys.exit(1)
        git_hash_object(args[1], write=True)
    else:
        git_hash_object(args[0])