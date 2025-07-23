import os
import shutil
import zlib

def read_object(sha1, type_):
    obj_path = os.path.join(".mygit", "objects", sha1[:2], sha1[2:])
    if not os.path.exists(obj_path):
        return None
    with open(obj_path, "rb") as f:
        compressed = f.read()
    data = zlib.decompress(compressed)
    header_end = data.find(b'\0')
    header = data[:header_end].decode()
    assert header.startswith(type_)
    return data[header_end+1:]

def restore_files_from_commit(commit_hash):
    # Cherche le commit dans commits.txt pour retrouver le tree
    if not os.path.exists("commits.txt"):
        return
    with open("commits.txt", encoding="utf-8") as f:
        content = f.read()
    commits = content.strip().split("\n\n")
    tree_hash = None
    for commit in reversed(commits):
        if f"Commit: {commit_hash}" in commit:
            for line in commit.splitlines():
                if line.startswith("Tree:"):
                    tree_hash = line.split(":", 1)[1].strip()
                    break
            break
    if not tree_hash:
        print("Impossible de retrouver le tree pour ce commit.")
        return

    # Lire l'objet tree
    tree_data = read_object(tree_hash, "tree")
    if tree_data is None:
        print("Impossible de lire l'objet tree.")
        return

    # Fichiers à restaurer
    files = []
    for line in tree_data.decode().splitlines():
        if line.startswith("blob "):
            _, blob_hash, filename = line.split(" ", 2)
            files.append((filename, blob_hash))

    # Déplacer les fichiers non présents dans le commit vers mon disque D dans : D:/TT
    wd_files = [f for f in os.listdir('.') if os.path.isfile(f) and not f.startswith('.') and f != 'commits.txt']
    tt_dir = "D:/TT"
    os.makedirs(tt_dir, exist_ok=True)
    filenames_in_commit = [filename for filename, _ in files]
    for f in wd_files:
        if f not in filenames_in_commit:
            try:
                shutil.move(f, os.path.join(tt_dir, f))
                print(f"Fichier déplacé vers {tt_dir} : {f}")
            except Exception as e:
                print(f"Erreur lors du déplacement de {f} : {e}")

    # Restaurer les fichiers du commit
    for filename, blob_hash in files:
        blob_data = read_object(blob_hash, "blob")
        if blob_data is not None:
            with open(filename, "wb") as f:
                f.write(blob_data)
            print(f"Fichier restauré : {filename}")
        else:
            print(f"Impossible de restaurer {filename} (blob manquant)")

def run(args):
    if not args:
        print("Usage: checkout <nom_branche>")
        return
    branch = args[0]
    branch_ref = os.path.join(".mygit", "refs", "heads", branch)
    if not os.path.exists(branch_ref):
        print(f"La branche '{branch}' n'existe pas.")
        return
    head_path = os.path.join(".mygit", "HEAD")
    with open(head_path, "w") as f:
        f.write(f"ref: refs/heads/{branch}\n")
    print(f"Branche courante : {branch}")

    # Restaure l'état du projet pour la branche
    with open(branch_ref) as f:
        last_commit_hash = f.read().strip()
    if last_commit_hash:
        restore_files_from_commit(last_commit_hash)
        print("État du projet restauré pour la branche.")
    else:
        print("Aucun commit sur cette branche, rien à restaurer.")