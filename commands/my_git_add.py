import os
import argparse
import hashlib
import zlib

def list_files_recursively(paths):
    all_files = []
    for path in paths:
        if os.path.isfile(path):
            all_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in files:
                    full_path = os.path.join(root, f)
                    if not os.path.basename(full_path).startswith('.') and ".mygit" not in full_path:
                        all_files.append(os.path.relpath(full_path))
    return all_files

def run(args):
    parser = argparse.ArgumentParser(prog="add", description="Ajoute des fichiers/dossiers à l'index (staging area)")
    parser.add_argument('files', nargs='*', help="Fichiers ou dossiers à ajouter")
    parser.add_argument('-n', '--dry-run', action='store_true', help="Ne rien ajouter, seulement montrer ce qui serait fait")
    parser.add_argument('-v', '--verbose', action='store_true', help="Afficher les fichiers ajoutés")
    parser.add_argument('-A', '--all', action='store_true', help="Ajouter tous les fichiers, y compris les suppressions")

    opts = parser.parse_args(args)

    if opts.all:
        files = []
        for root, _, filenames in os.walk('.'):
            if ".git" in root or ".mygit" in root:
                continue
            for f in filenames:
                full_path = os.path.join(root, f)
                if (
                    not f.startswith('.') and
                    not f.endswith('.pyc') and
                    "__pycache__" not in full_path
                    and ".git" not in full_path
                    and ".mygit" not in full_path
                ):
                    files.append(os.path.relpath(full_path))
    else:
        files = [
            f for f in list_files_recursively(opts.files)
            if "__pycache__" not in f and ".git" not in f and ".mygit" not in f
        ]

    if not files:
        print("Aucun fichier à ajouter.")
        return

    index_file = ".mygit/index"
    if os.path.exists(index_file):
        with open(index_file, "r") as f:
            index_files = set(line.strip() for line in f.readlines())
    else:
        index_files = set()

    new_files = [f for f in files if f not in index_files]

    for f in new_files:
        norm_path = f.replace("\\", "/") 
        if opts.dry_run:
            print(f"Ajouterais: {norm_path}")
        else:
            if opts.verbose:
                print(f"{norm_path} ajouté à l'index")
            try:
                with open(f, "rb") as file_content:
                    data = file_content.read()
                    header = f"blob {len(data)}\0".encode()
                    full_data = header + data
                    sha1 = hashlib.sha1(full_data).hexdigest()
                    obj_dir = os.path.join(".mygit", "objects", sha1[:2])
                    obj_path = os.path.join(obj_dir, sha1[2:])
                    os.makedirs(obj_dir, exist_ok=True)
                    if not os.path.exists(obj_path):
                        with open(obj_path, "wb") as fobj:
                            fobj.write(zlib.compress(full_data))
            except Exception as e:
                print(f"Erreur lors de la création du blob pour {f}: {e}")

    if not opts.dry_run and new_files:
        with open(index_file, "a") as f_index:
            for file in new_files:
                f_index.write(norm_path + '\n')

    if not opts.verbose and not opts.dry_run:
        print(f"{len(new_files)} fichier(s) ajouté(s) à l'index.")

    unique_files = set()
    for f in files:
        norm_path = f.replace("\\", "/")
        unique_files.add(norm_path)

    with open(index_file, "w") as f_index:
        for file in sorted(unique_files):
            f_index.write(file + "\n")