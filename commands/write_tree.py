import sys
import hashlib
import zlib
import os
from pathlib import Path
from collections import defaultdict

def run(argv):
    try:
        git_dir = Path(".mygit")
        if not git_dir.exists():
            print("fatal: not a git repository", file=sys.stderr)
            sys.exit(1)
        
        index_file = git_dir / "index"
        # Si il y a pas d'index on va créer un arbre vide
        if not index_file.exists():
            return create_empty_tree()
        
        entries = read_simple_index(index_file)
        tree_sha = create_tree_from_entries(entries)
        print(tree_sha)
        return tree_sha
    except Exception as e:
        print(f"fatal: {e}", file=sys.stderr)
        sys.exit(1)

def read_simple_index(index_file):
    try:
        with open(index_file, 'r') as f:
            file_paths = [line.strip() for line in f.readlines() if line.strip()]
        
        entries = []
        for file_path in file_paths:
            # Vérifier que le fichier existe encore
            if not os.path.exists(file_path):
                print(f"warning: fichier {file_path} dans l'index mais absent du disque", file=sys.stderr)
                continue
            
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                blob_header = f"blob {len(file_content)}\0".encode()
                blob_data = blob_header + file_content
                file_sha = hashlib.sha1(blob_data).hexdigest()
                
                # Stocker l'objet blob
                store_object(blob_data, file_sha)
                file_stat = os.stat(file_path)
                if file_stat.st_mode & 0o100:
                    mode = 0o100755
                else:
                    mode = 0o100644
                
                # Créer l'entrée pour l'arbre
                entry = {
                    'mode': mode,
                    'path': file_path,
                    'sha': file_sha,
                    'type': 'blob'
                }
                entries.append(entry)
            except Exception as e:
                print(f"error: impossible de lire {file_path}: {e}", file=sys.stderr)
                continue
        
        return entries
    except Exception as e:
        print(f"error: impossible de lire l'index: {e}", file=sys.stderr)
        return []

def create_tree_from_entries(entries):
    if not entries:
        return create_empty_tree()
    
    # Construire la hiérarchie des dossiers
    tree_structure = build_tree_structure(entries)
    
    # Créer récursivement les objets tree
    return create_tree_recursive(tree_structure)

def build_tree_structure(entries):
    tree = defaultdict(lambda: {'files': [], 'subdirs': defaultdict(lambda: {'files': [], 'subdirs': {}})})
    
    for entry in entries:
        path_parts = entry['path'].split('/')
        
        if len(path_parts) == 1:
            # Fichier à la racine
            tree['files'].append(entry)
        else:
            # Fichier dans un sous-dossier
            current_level = tree

            for i, part in enumerate(path_parts[:-1]):
                if part not in current_level['subdirs']:
                    current_level['subdirs'][part] = {'files': [], 'subdirs': {}}
                current_level = current_level['subdirs'][part]
            
            # Ajouter le fichier au bon niveau
            file_entry = entry.copy()
            file_entry['name'] = path_parts[-1]  # Juste le nom du fichier
            current_level['files'].append(file_entry)
    
    return tree

def create_tree_recursive(tree_structure):
    tree_entries = []
    
    # Ajouter les fichiers
    for file_entry in tree_structure['files']:
        name = file_entry.get('name', file_entry['path'])
        tree_entries.append({
            'mode': file_entry['mode'],
            'name': name,
            'sha': file_entry['sha'],
            'type': 'blob'
        })
    
    # Ajouter les sous-dossiers
    for dirname, subdir_structure in tree_structure['subdirs'].items():
        subdir_sha = create_tree_recursive(subdir_structure)
        tree_entries.append({
            'mode': 0o040000,  
            'name': dirname,
            'sha': subdir_sha,
            'type': 'tree'
        })
    
    tree_entries.sort(key=lambda x: x['name'])
    
    # Construire le contenu de l'arbre
    tree_content = b""
    for entry in tree_entries:
        mode = entry['mode']
        name = entry['name']
        sha = entry['sha']
        
        # Format d'entrée Git: mode(octal) + espace + nom + null + sha_binaire
        mode_str = f"{mode:o}".encode('ascii')
        name_bytes = name.encode('utf-8')
        sha_bytes = bytes.fromhex(sha)
        
        entry_data = mode_str + b' ' + name_bytes + b'\0' + sha_bytes
        tree_content += entry_data
    
    return write_tree_object(tree_content)

def create_empty_tree():
    tree_content = b""
    return write_tree_object(tree_content)

def write_tree_object(content):
    header = f"tree {len(content)}\0".encode('ascii')
    obj_content = header + content
    
    # Calculer le SHA-1
    sha = hashlib.sha1(obj_content).hexdigest()
    
    # Stocker l'objet
    store_object(obj_content, sha)
    
    return sha

def store_object(obj_content, sha):
    git_dir = Path(".mygit")
    obj_dir = git_dir / "objects" / sha[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    
    # Compresser avec zlib
    obj_file = obj_dir / sha[2:]
    if not obj_file.exists():
        compressed = zlib.compress(obj_content)
        obj_file.write_bytes(compressed)

if __name__ == "__main__":
    run(sys.argv[1:])
