import sys
import hashlib
import zlib
import os
from pathlib import Path

def run(argv):
    try:
        git_dir = Path(".mygit")
        if not git_dir.exists():
            print("fatal: not a git repository", file=sys.stderr)
            sys.exit(1)
            
        index_file = git_dir / "index"
        
        # Si pas d'index on va créer un arbre vide
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
                
                file_stat = os.stat(file_path)
                if file_stat.st_mode & 0o100:  
                    mode = 0o100755
                else:
                    mode = 0o100644
                
                # Créer l'entrée pour l'arbre
                entry = {
                    'mode': mode,
                    'name': file_path,
                    'sha': file_sha
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
        
    # Trier les entrées par nom 
    entries.sort(key=lambda x: x['name'])
    
    # Construire le contenu de l'arbre 
    tree_content = b""
    
    for entry in entries:
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
    
    git_dir = Path(".mygit")
    obj_dir = git_dir / "objects" / sha[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    
    # compresser avec zlib 
    obj_file = obj_dir / sha[2:]
    if not obj_file.exists():
        compressed = zlib.compress(obj_content)
        obj_file.write_bytes(compressed)
        
    return sha

if __name__ == "__main__":
    run(sys.argv[1:])
