import os
import sys
import argparse
from datetime import datetime
import hashlib
import getpass
import zlib

def hash_object(data, type_="commit", write=True):
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    header = f"{type_} {len(data)}\0".encode()
    full_data = header + data
    sha1 = hashlib.sha1(full_data).hexdigest()
    
    if write:
        obj_dir = os.path.join(".mygit", "objects", sha1[:2])
        obj_path = os.path.join(obj_dir, sha1[2:])
        os.makedirs(obj_dir, exist_ok=True)
        
        if not os.path.exists(obj_path):
            with open(obj_path, "wb") as f:
                f.write(zlib.compress(full_data))
    
    return sha1

def object_exists(sha):
    if len(sha) != 40:
        return False
    
    obj_path = os.path.join(".mygit", "objects", sha[:2], sha[2:])
    return os.path.exists(obj_path)

def read_object(sha):
    obj_path = os.path.join(".mygit", "objects", sha[:2], sha[2:])
    
    if not os.path.exists(obj_path):
        return None, None
    
    try:
        with open(obj_path, 'rb') as f:
            compressed_data = f.read()
        
        
        try:
            decompressed = zlib.decompress(compressed_data)
        except:
            decompressed = compressed_data
        
        
        null_pos = decompressed.find(b'\0')
        if null_pos > 0:
            header = decompressed[:null_pos].decode('utf-8')
            content = decompressed[null_pos + 1:]
            obj_type, size = header.split(' ')
            return obj_type, content
        
        return None, None
    except Exception:
        return None, None

def build_commit_object(tree_sha, parent_sha, author, message, date):
    lines = [f"tree {tree_sha}"]
    
    if parent_sha:
        lines.append(f"parent {parent_sha}")
    
    lines.append(f"author {author} {date}")
    lines.append(f"committer {author} {date}")
    lines.append("")  
    lines.append(message)
    
    return "\n".join(lines)

def run(args):
    # Vérifier que nous sommes dans un dépôt Git
    if not os.path.exists(".mygit"):
        print("fatal: not a git repository", file=sys.stderr)
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        prog="commit-tree", 
        description="Crée un nouvel objet commit"
    )
    parser.add_argument('tree', help="SHA de l'arbre à committer")
    parser.add_argument('-p', '--parent', help="SHA du commit parent")
    parser.add_argument('-m', '--message', required=True, help="Message du commit")
    parser.add_argument('--author', help="Auteur du commit (par défaut: utilisateur courant)")
    
    try:
        opts = parser.parse_args(args)
    except SystemExit as e:
        sys.exit(e.code)
    
    tree_sha = opts.tree
    parent_sha = opts.parent
    message = opts.message
    author = opts.author if opts.author else getpass.getuser()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Vérifier que l'arbre existe
    if not object_exists(tree_sha):
        print(f"fatal: not a valid object name {tree_sha}", file=sys.stderr)
        sys.exit(1)
    
    # Vérifier que c'est bien un arbre
    obj_type, _ = read_object(tree_sha)
    if obj_type != "tree":
        print(f"fatal: {tree_sha} is not a tree object", file=sys.stderr)
        sys.exit(1)
    
    # Vérifier le parent
    if parent_sha:
        if not object_exists(parent_sha):
            print(f"fatal: not a valid object name {parent_sha}", file=sys.stderr)
            sys.exit(1)
        
        parent_type, _ = read_object(parent_sha)
        if parent_type != "commit":
            print(f"fatal: {parent_sha} is not a commit object", file=sys.stderr)
            sys.exit(1)
    
    # Construire l'objet commit
    commit_content = build_commit_object(tree_sha, parent_sha, author, message, date)
    
    # Créer l'objet commit
    commit_sha = hash_object(commit_content, "commit", write=True)
    
    # Afficher le SHA du commit créé
    print(commit_sha)
    
    return commit_sha

if __name__ == "__main__":
    run(sys.argv[1:])
