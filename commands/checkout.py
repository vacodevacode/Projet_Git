import os
import shutil
import zlib

def read_object(sha1, type_=None):
    obj_path = os.path.join(".mygit", "objects", sha1[:2], sha1[2:])
    if not os.path.exists(obj_path):
        return None
    with open(obj_path, "rb") as f:
        compressed = f.read()
    data = zlib.decompress(compressed)
    header_end = data.find(b'\0')
    header = data[:header_end].decode()
    if type_:
        assert header.startswith(type_)
    obj_type = header.split()[0]
    return obj_type, data[header_end+1:]

def restore_tree(tree_hash, base_path=".", restored_files=None):
    if restored_files is None:
        restored_files = []
    obj_type, tree_data = read_object(tree_hash)
    for line in tree_data.decode().splitlines():
        if line.startswith("blob "):
            _, blob_hash, filename = line.split(" ", 2)
            file_path = os.path.join(base_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True) if os.path.dirname(file_path) else None
            blob_type, blob_data = read_object(blob_hash, "blob")
            with open(file_path, "wb") as f:
                f.write(blob_data)
            restored_files.append(file_path)
        elif line.startswith("tree "):
            _, sub_tree_hash, dirname = line.split(" ", 2)
            dir_path = os.path.join(base_path, dirname)
            os.makedirs(dir_path, exist_ok=True)
            restore_tree(sub_tree_hash, dir_path, restored_files)
    return restored_files

def restore_files_from_commit(commit_hash):
    # Lire l'objet commit
    _, commit_data = read_object(commit_hash, "commit")
    lines = commit_data.decode().splitlines()
    tree_hash = None
    for line in lines:
        if line.startswith("tree "):
            tree_hash = line.split(" ", 1)[1].strip()
            break
    if not tree_hash:
        print("Impossible de retrouver le tree pour ce commit.")
        return

    
    wd_files = []
    excluded_dirs = {".mygit", ".git", ".github", "__pycache__"}
    excluded_files = {"commits.txt"}

    for root, dirs, files in os.walk("."):
        # Exclure les dossiers interdits du déplacement 
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for f in files:
            if f in excluded_files:
                continue
            full_path = os.path.relpath(os.path.join(root, f))
            # Exclure les fichiers dans les dossiers pas qu'on doit pas déplacer 
            if any(ex in full_path.split(os.sep) for ex in excluded_dirs):
                continue
            wd_files.append(full_path)

    # Récupération de tous nos fichiers du tree (récursivement)
    files_in_commit = []
    def collect_files(tree_hash, base_path=""):
        obj_type, tree_data = read_object(tree_hash)
        for line in tree_data.decode().splitlines():
            if line.startswith("blob "):
                _, _, filename = line.split(" ", 2)
                files_in_commit.append(os.path.join(base_path, filename))
            elif line.startswith("tree "):
                _, sub_tree_hash, dirname = line.split(" ", 2)
                collect_files(sub_tree_hash, os.path.join(base_path, dirname))
    collect_files(tree_hash)

    # Déplacer les fichiers non présents dans le commit vers D:/TT
    tt_dir = "D:/TT"
    os.makedirs(tt_dir, exist_ok=True)
    for f in wd_files:
        if f not in files_in_commit:
            try:
                shutil.move(f, os.path.join(tt_dir, os.path.basename(f)))
                print(f"Fichier déplacé vers {tt_dir} : {f}")
            except Exception as e:
                print(f"Erreur lors du déplacement de {f} : {e}")

    # Restaurer toute l'arborescence
    restored = restore_tree(tree_hash)
    print("\n🧾 Fichiers restaurés :")
    for f in restored:
        print(" -", f)

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