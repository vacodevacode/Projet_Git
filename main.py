#!/usr/bin/env python3
import sys
import traceback

def main():
    try:
        if len(sys.argv) < 2:
            print("usage: mygit <command> [<args>]")
            sys.exit(1)

        command = sys.argv[1]

        if command == "hash-object":
            from commands import hash_object
            hash_object.run(sys.argv[2:])
        elif command == "my_git_init":
            from commands import my_git_init
            my_git_init.run(sys.argv[2:])
        elif command == "git_cat_file":
            from commands import git_cat_file
            git_cat_file.run(sys.argv[2:])
        elif command == "my_git_add":
            from commands import my_git_add
            my_git_add.run(sys.argv[2:])
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except ImportError as e:
        print(f"Error: could not import module for command '{command}'.")
        print(f"Details: {e}")
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
    elif command == "reset":
        from commands import reset
        reset.run(sys.argv[2:])               
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
