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
    elif command == "add":
        from commands import add
        add.run(sys.argv[2:]) 
    elif command == "commit":
        from commands import commit
        commit.run(sys.argv[2:])
    elif command == "push":
        from commands import push
        push.run(sys.argv[2:])
    elif command == "branch":
        from commands import branch
        branch.run(sys.argv[2:])
    elif command == "checkout":
        from commands import checkout 
        checkout.run(sys.argv[2:]) 
    elif command == "log":
        from commands import log
        log.run(sys.argv[2:]) 
    elif command == "rm":
        from commands import rm
        rm.run(sys.argv[2:])
    elif command == "merge":
        from commands import merge
        merge.run(sys.argv[2:]) 
    elif command == "status":
        from commands import status
        status.run(sys.argv[2:])  
    elif command == "reset":
        from commands import reset
        reset.run(sys.argv[2:])               
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()