import sys
import hashlib
import zlib
import time
import os
from pathlib import Path

def run(argv):
    try:
        if len(argv) < 3:
            print("usage: git commit-tree <tree> -m <message> [-p <parent>]", file=sys.stderr)
            sys.exit(1)
        
        tree_sha = argv[0]
        message = None
        parent_sha = None
        i = 1       
        while i < len(argv):
            if argv[i] == "-m" and i + 1 < len(argv):
                message = argv[i + 1]
                i += 2
            elif argv[i] == "-p" and i + 1 < len(argv):
                parent_sha = argv[i + 1]
                i += 2
            else:
                i += 1
        
        if not message:
            print("fatal: message required", file=sys.stderr)
            sys.exit(1)
        
        # Ici on va venir créer le commit 
        commit_sha = create_commit_object(tree_sha, message, parent_sha)
        print(commit_sha)
        
    except Exception as e:
        print(f"fatal: {e}", file=sys.stderr)
        sys.exit(1)

def create_commit_object(tree_sha, message, parent_sha=None):
    """Crée un objet commit (format Git standard)"""
    
    # Récupérer les informations de l'auteur
    author_name = os.environ.get('GIT_AUTHOR_NAME', 'Unknown')
    author_email = os.environ.get('GIT_AUTHOR_EMAIL', 'unknown@example.com')
    timestamp = int(time.time())
    timezone = "+0000"
    author_line = f"{author_name} <{author_email}> {timestamp} {timezone}"
    
    # Construire le contenu du commit 
    commit_content = f"tree {tree_sha}\n"
    if parent_sha:
        commit_content += f"parent {parent_sha}\n"
    commit_content += f"author {author_line}\n"
    commit_content += f"committer {author_line}\n"
    commit_content += f"\n{message}\n"
    
    obj_content = f"commit {len(commit_content)}\0{commit_content}"
    sha = hashlib.sha1(obj_content.encode()).hexdigest()
    
    git_dir = Path(".mygit")
    obj_dir = git_dir / "objects" / sha[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    
    # Compresser avec zlib 
    obj_file = obj_dir / sha[2:]
    if not obj_file.exists():
        compressed = zlib.compress(obj_content.encode())
        obj_file.write_bytes(compressed)
    
    return sha

if __name__ == "__main__":
    run(sys.argv[1:])
