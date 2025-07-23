import sys
import zlib
import hashlib
from pathlib import Path
from typing import Optional, List, Union
from datetime import datetime


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


def resolve_ref(git_dir: Path, ref: str) -> Optional[str]:
    """Résout une référence vers son SHA-1."""
    # Si c'est déjà un SHA-1, le retourner
    if len(ref) == 40 and all(c in '0123456789abcdef' for c in ref):
        return ref
    
    # Si c'est HEAD
    if ref == "HEAD":
        head_file = git_dir / "HEAD"
        if head_file.exists():
            head_content = safe_read_text(head_file)
            if head_content.startswith("ref: "):
                # HEAD pointe vers une branche
                branch_ref = head_content[5:]  # Enlever "ref: "
                return resolve_ref(git_dir, branch_ref)
            else:
                # HEAD pointe directement vers un commit
                return head_content
    
    # Si c'est une référence complète (refs/heads/main)
    if ref.startswith("refs/"):
        ref_file = git_dir / ref
        if ref_file.exists():
            return safe_read_text(ref_file)
    
    # Si c'est juste un nom de branche
    branch_file = git_dir / "refs" / "heads" / ref
    if branch_file.exists():
        return safe_read_text(branch_file)
    
    return None


def read_git_object(git_dir: Path, oid: str) -> dict:
    """Lit un objet Git depuis le disque et retourne ses informations."""
    objects_dir = git_dir / "objects"
    obj_dir = objects_dir / oid[:2]
    obj_file = obj_dir / oid[2:]
    print(f"Reading object {oid} from {obj_file}")
    if not obj_file.exists():
        raise FileNotFoundError(f"Object {oid} not found")
    
    # Lire et décompresser
    compressed = obj_file.read_bytes()
    try:
        serialized = zlib.decompress(compressed)
    except zlib.error:
        raise ValueError(f"Object {oid} is corrupted")
    
    # Parser l'en-tête
    null_pos = serialized.find(b'\0')
    if null_pos == -1:
        raise ValueError(f"Object {oid} has invalid format")
    
    header = serialized[:null_pos].decode('utf-8', errors='replace')
    content = serialized[null_pos + 1:]
    
    try:
        obj_type, size_str = header.split(' ', 1)
        expected_size = int(size_str)
    except ValueError:
        raise ValueError(f"Object {oid} has invalid header: {header}")
    
    if len(content) != expected_size:
        raise ValueError(f"Object {oid} size mismatch")
    
    return {
        'type': obj_type,
        'content': content,
        'size': expected_size
    }


def parse_commit(content: bytes) -> dict:
    """Parse le contenu d'un commit Git."""
    text = content.decode('utf-8', errors='replace')
    lines = text.split('\n')
    
    tree_oid = None
    parent_oids = []
    author = None
    author_date = None
    committer = None
    committer_date = None
    message_start = 0
    
    for i, line in enumerate(lines):
        if line.startswith("tree "):
            tree_oid = line[5:]
        elif line.startswith("parent "):
            parent_oids.append(line[7:])
        elif line.startswith("author "):
            # Format: author Name <email> timestamp timezone
            parts = line[7:].rsplit(' ', 2)
            if len(parts) >= 3:
                author = parts[0]
                try:
                    timestamp = int(parts[1])
                    author_date = datetime.fromtimestamp(timestamp)
                except (ValueError, OSError):
                    author_date = None
            else:
                author = line[7:]
        elif line.startswith("committer "):
            # Format: committer Name <email> timestamp timezone
            parts = line[10:].rsplit(' ', 2)
            if len(parts) >= 3:
                committer = parts[0]
                try:
                    timestamp = int(parts[1])
                    committer_date = datetime.fromtimestamp(timestamp)
                except (ValueError, OSError):
                    committer_date = None
            else:
                committer = line[10:]
        elif line == "":
            message_start = i + 1
            break
    
    message = '\n'.join(lines[message_start:])
    
    return {
        'tree_oid': tree_oid,
        'parent_oids': parent_oids,
        'author': author,
        'author_date': author_date,
        'committer': committer,
        'committer_date': committer_date,
        'message': message
    }


def format_commit_oneline(commit_oid: str, commit_data: dict) -> str:
    """Formate un commit sur une ligne."""
    short_oid = commit_oid[:7]
    first_line = commit_data['message'].split('\n')[0] if commit_data['message'] else ""
    return f"{short_oid} {first_line}"


def format_commit_detailed(commit_oid: str, commit_data: dict) -> str:
    """Formate un commit avec tous les détails."""
    lines = []
    lines.append(f"commit {commit_oid}")
    
    if commit_data['author']:
        if commit_data['author_date']:
            date_str = commit_data['author_date'].strftime("%a %b %d %H:%M:%S %Y")
            lines.append(f"Author: {commit_data['author']}")
            lines.append(f"Date:   {date_str}")
        else:
            lines.append(f"Author: {commit_data['author']}")
    
    lines.append("")
    
    # Indenter le message
    if commit_data['message']:
        for line in commit_data['message'].split('\n'):
            lines.append(f"    {line}")
    
    lines.append("")
    return '\n'.join(lines)


def run_log(args: List[str] = None):
    """Exécute la commande log de manière indépendante."""
    if args is None:
        args = []
    
    # Parser les arguments
    max_count = None
    oneline = False
    start_ref = "HEAD"
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--oneline":
            oneline = True
        elif arg.startswith("-n") or arg.startswith("--max-count="):
            if arg.startswith("--max-count="):
                try:
                    max_count = int(arg.split("=", 1)[1])
                except ValueError:
                    print(f"Error: Invalid max-count value: {arg}")
                    sys.exit(1)
            elif arg == "-n" and i + 1 < len(args):
                try:
                    max_count = int(args[i + 1])
                    i += 1  # Skip next argument
                except ValueError:
                    print(f"Error: Invalid max-count value: {args[i + 1]}")
                    sys.exit(1)
            elif len(arg) > 2:  # -n5 format
                try:
                    max_count = int(arg[2:])
                except ValueError:
                    print(f"Error: Invalid max-count value: {arg}")
                    sys.exit(1)
        elif not arg.startswith("-"):
            # C'est probablement une référence (branche, commit, etc.)
            start_ref = arg
        i += 1
    
    try:
        # Trouver le repository
        repo_root = find_git_repository()
        git_dir = repo_root / ".git"
        
        # Commencer depuis la référence spécifiée
        current_oid = resolve_ref(git_dir, start_ref)
        if not current_oid:
            print(f"Error: Could not resolve reference '{start_ref}'")
            sys.exit(1)
        
        # Parcourir l'historique
        visited = set()
        count = 0
        
        while current_oid and current_oid not in visited:
            # Vérifier la limite de count
            if max_count is not None and count >= max_count:
                break
            
            visited.add(current_oid)
            
            try:
                # Lire l'objet commit
                obj_data = read_git_object(git_dir, current_oid)
                
                # Vérifier que c'est bien un commit
                if obj_data['type'] != 'commit':
                    print(f"Error: Object {current_oid} is not a commit")
                    break
                
                # Parser le commit
                commit_data = parse_commit(obj_data['content'])
                
                # Afficher les informations du commit
                if oneline:
                    print(format_commit_oneline(current_oid, commit_data))
                else:
                    print(format_commit_detailed(current_oid, commit_data))
                
                count += 1
                
                # Passer au parent (pour simplifier, on prend juste le premier)
                if commit_data['parent_oids']:
                    current_oid = commit_data['parent_oids'][0]
                else:
                    break
                    
            except FileNotFoundError:
                print(f"Error: Commit {current_oid} not found")
                break
            except Exception as e:
                print(f"Error reading commit {current_oid}: {e}")
                break
                
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Quand appelé directement, utiliser sys.argv
    run_log(sys.argv[1:])
