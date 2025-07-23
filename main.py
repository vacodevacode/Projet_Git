#!/usr/bin/env python3
import sys

def main():
    if len(sys.argv) < 2:
        print("usage: mygit <command> [<args>]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "hash-object":
        from commands import hash_object
        hash_object.run(sys.argv[2:])
    elif command == "init":
        from commands import init
        init.run(sys.argv[2:])
    elif command == "cat-file":
        from commands import git_cat_file
        git_cat_file.run(sys.argv[2:])
        
    elif command == "merge":
        from commands import merge
        merge.run_merge(sys.argv[2:])
    elif command == "status":
        from commands import status
        status.run_status(sys.argv[2:])
    elif command == "log":
        from commands import log
        log.run_log(sys.argv[2:])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()




























    