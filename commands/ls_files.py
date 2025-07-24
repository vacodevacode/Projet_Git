import os
import sys
import argparse
import hashlib
from pathlib import Path

def hash_file_content(file_path):
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        header = f"blob {len(content)}\0".encode()
        full_data = header + content
        return hashlib.sha1(full_data).hexdigest()
    except:
        return "0" * 40

def get_file_mode(file_path):
    try:
        file_stat = os.stat(file_path)
        if file_stat.st_mode & 0o100:
            return "100755"  
        else:
            return "100644"  
    except:
        return "100644"

# Lit l'index et retourne la liste des fichiers
def read_index():
   
    index_file = Path(".mygit/index")
    if not index_file.exists():
        return []
    
    try:
        with open(index_file, 'r') as f:
            files = [line.strip() for line in f.readlines() if line.strip()]
        return files
    except Exception as e:
        print(f"error: impossible de lire l'index: {e}", file=sys.stderr)
        return []

def get_untracked_files():
    indexed_files = set(read_index())
    untracked = []
    
    # Parcourir récursivement le répertoire courant
    for root, dirs, files in os.walk("."):
        # Ignorer le dossier .mygit
        if ".mygit" in dirs:
            dirs.remove(".mygit")
        
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), ".")
            file_path = file_path.replace("\\", "/")
            
            if file_path not in indexed_files:
                untracked.append(file_path)
    
    return sorted(untracked)

def get_modified_files():
    indexed_files = read_index()
    modified = []
    
    for file_path in indexed_files:
        if os.path.exists(file_path):
            # Comparer le SHA actuel avec celui qui serait dans l'index
            current_sha = hash_file_content(file_path)
            pass
        else:
            modified.append(f"deleted: {file_path}")
    
    return modified

def list_cached_files(show_stage=False):
    files = read_index()
    
    if not files:
        return
    
    for file_path in files:
        if show_stage:
            # Format avec informations détaillées
            if os.path.exists(file_path):
                mode = get_file_mode(file_path)
                sha = hash_file_content(file_path)
                print(f"{mode} {sha} 0\t{file_path}")
            else:
                print(f"100644 {'0' * 40} 0\t{file_path}")
        else:
            # Format simple
            print(file_path)

def list_other_files():
    untracked = get_untracked_files()
    for file_path in untracked:
        print(file_path)

def run(args):
    # Vérifier que nous sommes dans un dépôt Git
    if not os.path.exists(".mygit"):
        print("fatal: not a git repository", file=sys.stderr)
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        prog="ls-files",
        description="Affiche les informations sur les fichiers dans l'index et l'arbre de travail"
    )
    
    parser.add_argument('-c', '--cached', action='store_true', default=True,
                       help="Affiche les fichiers dans l'index (par défaut)")
    parser.add_argument('-o', '--others', action='store_true',
                       help="Affiche les fichiers non suivis")
    parser.add_argument('-m', '--modified', action='store_true',
                       help="Affiche les fichiers modifiés")
    parser.add_argument('-s', '--stage', action='store_true',
                       help="Affiche les informations de staging (mode, SHA, stage, nom)")
    parser.add_argument('-z', action='store_true',
                       help="Termine les lignes par NUL au lieu de LF")
    parser.add_argument('pathspec', nargs='*',
                       help="Limiter la sortie aux chemins correspondants")
    
    try:
        opts = parser.parse_args(args)
    except SystemExit as e:
        sys.exit(e.code)
    
    if not (opts.others or opts.modified):
        opts.cached = True
    
    if opts.cached:
        list_cached_files(show_stage=opts.stage)
    
    if opts.others:
        list_other_files()
    
    if opts.modified:
        modified = get_modified_files()
        for item in modified:
            print(item)

if __name__ == "__main__":
    run(sys.argv[1:])
