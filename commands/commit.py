import os
import argparse
from datetime import datetime
import hashlib
import getpass
import zlib

def get_current_branch():
    head_path = os.path.join(".mygit", "HEAD")
    if os.path.exists(head_path):
        with open(head_path) as f:
            line = f.read().strip()
            if line.startswith("ref:"):
                return line.split("/")[-1]
    return "main"

def hash_object(data, type_="blob", write=True):
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

def build_tree(files):
    entries = []
    for f in files:
        with open(f, "rb") as file_content:
            data = file_content.read()
            blob_hash = hash_object(data, "blob", write=True)
            entries.append(f"blob {blob_hash} {f}")
    tree_data = "\n".join(entries).encode()
    tree_hash = hash_object(tree_data, "tree", write=True)
    return tree_hash, entries

def build_commit(tree_hash, parent_hash, author, message, date):
    lines = [
        f"tree {tree_hash}",
    ]
    if parent_hash:
        lines.append(f"parent {parent_hash}")
    lines.append(f"author {author} {date}")
    lines.append(f"committer {author} {date}")
    lines.append("")
    lines.append(message)
    commit_data = "\n".join(lines).encode()
    commit_hash = hash_object(commit_data, "commit", write=True)
    return commit_hash, commit_data

def run(args):
    parser = argparse.ArgumentParser(prog="commit", description="Enregistre les modifications indexées")
    parser.add_argument('-m', '--message', required=True, help="Message du commit")
    parser.add_argument('--author', help="Auteur du commit (par défaut: utilisateur courant)")
    opts = parser.parse_args(args)

    index_file = os.path.join(".mygit", "index")
    if not os.path.exists(index_file):
        print("Aucun fichier indexé à committer.")
        return

    with open(index_file, "r") as f:
        files = [line.strip() for line in f if line.strip()]

    if not files:
        print("Aucun fichier indexé à committer.")
        return

    author = opts.author if opts.author else getpass.getuser()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Récupérer le parent (dernier commit de la branche)
    branch_ref = os.path.join(".mygit", "refs", "heads", get_current_branch())
    parent_hash = None
    if os.path.exists(branch_ref):
        with open(branch_ref) as f:
            parent_hash = f.read().strip() or None

    # Créer l'objet tree
    tree_hash, tree_entries = build_tree(files)

    # Créer l'objet commit
    commit_hash, commit_data = build_commit(tree_hash, parent_hash, author, opts.message, date)

    # Écrit le hash du commit dans la branche courante
    with open(branch_ref, "w") as f:
        f.write(commit_hash)

    # Pour l'historique simple (pour le front), on garde commits.txt
    with open("commits.txt", "a", encoding="utf-8") as f:
        f.write(f"Commit: {commit_hash}\n")
        f.write(f"Date: {date}\n")
        f.write(f"Auteur: {author}\n")
        f.write(f"Message: {opts.message}\n")
        f.write(f"Tree: {tree_hash}\n")
        f.write("Fichiers:\n")
        for entry in tree_entries:
            # Format: blob <hash> <filename>
            f.write(f"  - {entry}\n")
        f.write("\n")

    print(f"Commit {commit_hash[:7]} effectué par {author} avec message : \"{opts.message}\" ({len(files)} fichier(s)).")