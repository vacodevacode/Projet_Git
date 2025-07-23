import sys
import os
# import json
import hashlib
import struct # Pour parser les fichiers binaires
from pathlib import Path
from typing import Dict, Set, List, Union

def safe_read_text(file_path: Path, encoding: str = 'utf-8') -> str:
    """Lecture sécurisée d'un fichier texte avec gestion d'erreurs."""
    try:
        content = file_path.read_text(encoding=encoding)
        if isinstance(content, list):
            content = '\n'.join(str(item) for item in content)
        elif not isinstance(content, str):
            content = str(content)
        return content.strip()
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding='latin-1')
            if isinstance(content, list):
                content = '\n'.join(str(item) for item in content)
            elif not isinstance(content, str):
                content = str(content)
            return content.strip()
        except Exception:
            return ""

def find_git_repository(start_path: Path = None) -> Path:
    """Trouve le repository Git en remontant l'arborescence."""
    if start_path is None:
        start_path = Path.cwd()
    
    current = start_path.resolve()
    
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    
    raise RuntimeError("Not in a git repository")

def get_relative_path(file_path: Path, repo_root: Path) -> str:
    """Retourne le chemin relatif d'un fichier par rapport à la racine du repository."""
    abs_file_path = file_path.resolve()
    abs_repo_root = repo_root.resolve()
    
    try:
        return str(abs_file_path.relative_to(abs_repo_root)).replace('\\', '/') # Normaliser les chemins
    except ValueError:
        return file_path.name.replace('\\', '/') # Normaliser les chemins

def read_gitignore(repo_root: Path) -> Set[str]:
    """Lit le fichier .gitignore et retourne les patterns à ignorer."""
    gitignore_file = repo_root / ".gitignore"
    patterns = set()
    
    if gitignore_file.exists():
        try:
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.add(line)
        except UnicodeDecodeError:
            with open(gitignore_file, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.add(line)
    
    return patterns

def should_ignore(file_path: str, gitignore_patterns: Set[str]) -> bool:
    """Vérifie si un fichier doit être ignoré selon les patterns .gitignore."""
    import fnmatch
    
    for pattern in gitignore_patterns:
        # Gérer les patterns de répertoire (ex: 'tmp/')
        if pattern.endswith('/'):
            if file_path.startswith(pattern) or file_path == pattern.rstrip('/'):
                return True
        # Gérer les patterns de fichiers (ex: '*.log')
        if fnmatch.fnmatch(file_path, pattern):
            return True
    
    return False

def calculate_file_hash(file_path: Path) -> str:
    """Calcule le hash SHA-1 d'un fichier comme Git le fait."""
    try:
        content = file_path.read_bytes()
        header = f"blob {len(content)}\0".encode('utf-8')
        full_content = header + content
        return hashlib.sha1(full_content).hexdigest()
    except (OSError, IOError):
        return ""

def load_index(git_dir: Path) -> Dict[str, Dict[str, str]]:
    """Charge l'index Git en parsant le fichier binaire .git/index."""
    index_file = git_dir / "index"
    if not index_file.exists():
        return {}

    indexed_files = {}
    try:
        with open(index_file, 'rb') as f:
            content = f.read()

        # Vérifier l'en-tête (DIRC)
        signature = content[0:4]
        if signature != b'DIRC':
            print(f"DEBUG: Invalid index signature: {signature}")
            return {}

        # Lire la version et le nombre d'entrées
        version, num_entries = struct.unpack('!II', content[4:12])
        # print(f"DEBUG: Index version: {version}, num_entries: {num_entries}") # Décommenter pour debug

        offset = 12 # Début des entrées après l'en-tête

        for _ in range(num_entries):
            # Lire la partie fixe de l'entrée (62 octets)
            # ctime (8), mtime (8), dev (4), ino (4), mode (4), uid (4), gid (4), size (4), sha1 (20), flags (2)
            fixed_entry_data = content[offset : offset + 62]
            if len(fixed_entry_data) < 62:
                print(f"DEBUG: Incomplete entry data at offset {offset}. Expected 62 bytes, got {len(fixed_entry_data)}")
                break # Fichier corrompu ou fin inattendue

            # Extraire le SHA-1 et les flags
            sha1_bytes = fixed_entry_data[40:60]
            flags = struct.unpack('!H', fixed_entry_data[60:62])[0] # Unpack comme unsigned short (2 octets)
            
            sha1 = sha1_bytes.hex()
            
            # La longueur du chemin est les 12 premiers bits des flags
            path_length = flags & 0xFFF 
            
            # Lire le nom du chemin (jusqu'à la longueur spécifiée par les flags)
            path_start = offset + 62
            path_end = path_start + path_length
            
            if path_end > len(content):
                print(f"DEBUG: Path length exceeds content length for entry at offset {offset}")
                break

            path_name = content[path_start:path_end].decode('utf-8', errors='replace')
            
            # Après le nom du chemin, il y a un octet nul (terminateur)
            # Puis des octets nuls pour le padding (alignement sur 8 octets)
            
            # Longueur totale de l'entrée (partie fixe + nom du chemin + 1 octet nul)
            entry_total_len = 62 + path_length + 1 
            
            # Calcul du padding pour aligner sur 8 octets
            padding_len = (8 - (entry_total_len % 8)) % 8
            
            # Mettre à jour l'offset pour la prochaine entrée
            offset += entry_total_len + padding_len
            
            if offset > len(content):
                print(f"DEBUG: Calculated next offset {offset} exceeds content length {len(content)}")
                break

            indexed_files[path_name] = {'oid': sha1}
        
        # Ignorer le checksum final pour l'instant
        return indexed_files

    except Exception as e:
        print(f"ERROR: Failed to load index: {e}")
        import traceback
        traceback.print_exc()
        return {}

def get_current_branch(git_dir: Path) -> str:
    """Retourne le nom de la branche courante."""
    head_file = git_dir / "HEAD"
    if head_file.exists():
        try:
            head_content = safe_read_text(head_file)
            if head_content.startswith("ref: refs/heads/"):
                return head_content[16:]  # Enlever "ref: refs/heads/"
        except Exception:
            pass
    return "HEAD"

def run_status(args: List[str] = None) -> None:
    """Exécute la commande status de manière indépendante."""
    if args is None:
        args = []
    
    try:
        # Trouver le repository
        repo_root = find_git_repository()
        git_dir = repo_root / ".git"
        
        # Charger l'index (maintenant binaire)
        index_data = load_index(git_dir)
        
        # Lire .gitignore
        gitignore_patterns = read_gitignore(repo_root)
        
        # Initialiser les ensembles de fichiers
        staged_files = set(index_data.keys()) # Fichiers dans l'index
        modified_files = set() # Fichiers modifiés mais non stagés
        untracked_files = set() # Nouveaux fichiers non suivis
        
        # Parcourir tous les fichiers du working directory
        for root, dirs, files in os.walk(repo_root):
            # Ignorer le dossier .git
            if '.git' in dirs:
                dirs.remove('.git')
            
            root_path = Path(root)
            for filename in files:
                file_path = root_path / filename
                rel_path = get_relative_path(file_path, repo_root)
                
                # Ignorer les fichiers selon .gitignore
                if should_ignore(rel_path, gitignore_patterns):
                    continue
                
                if rel_path in index_data:
                    # Fichier dans l'index - vérifier s'il est modifié
                    index_entry = index_data[rel_path]
                    current_hash = calculate_file_hash(file_path)
                    
                    if current_hash and current_hash != index_entry.get('oid', ''):
                        modified_files.add(rel_path)
                    # Si le fichier est modifié, il n'est plus "staged" dans le sens où il a des changements non stagés
                    # On le retire de staged_files pour ne pas l'afficher comme "new file" s'il est modifié
                    if rel_path in staged_files and current_hash != index_entry.get('oid', ''):
                        staged_files.discard(rel_path) # Retirer si modifié
                else:
                    # Fichier pas dans l'index - c'est un untracked
                    untracked_files.add(rel_path)
        
        # Les fichiers restants dans staged_files sont ceux qui sont stagés et non modifiés depuis le stage
        # Ou les nouveaux fichiers qui ont été stagés
        
        # Afficher le statut
        print("On branch", get_current_branch(git_dir))
        print()
        
        if staged_files:
            print("Changes to be committed:")
            for file_path in sorted(staged_files):
                # Pour simplifier, on affiche toujours "new file" ou "modified"
                # Une implémentation complète distinguerait "new file", "modified", "deleted"
                # en comparant l'index avec le HEAD du commit.
                # Pour l'instant, si c'est dans staged_files, c'est un changement à commiter.
                print(f"  new file:   {file_path}") 
            print()
        
        if modified_files:
            print("Changes not staged for commit:")
            for file_path in sorted(modified_files):
                print(f"  modified:   {file_path}")
            print()
        
        if untracked_files:
            print("Untracked files:")
            for file_path in sorted(untracked_files):
                print(f"  {file_path}")
            print()
        
        if not staged_files and not modified_files and not untracked_files:
            print("Working tree clean")
                
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_status(sys.argv[1:])
