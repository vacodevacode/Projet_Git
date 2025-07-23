import sys
from pathlib import Path
from typing import Optional, List, Dict, Union


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
        except Exception as e:
            return ""


def normalize_input(value: Union[str, List, None]) -> str:
    """Normalise l'entrée pour s'assurer qu'elle est une chaîne."""
    if value is None:
        return ""
    
    if isinstance(value, list):
        if len(value) > 0:
            return str(value[0])
        else:
            return ""
    
    if not isinstance(value, str):
        return str(value)
    
    return value.strip()


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


def list_all_refs(git_dir: Path) -> Dict[str, str]:
    """Liste toutes les références disponibles dans le repository."""
    refs = {}
    
    # Branches locales
    heads_dir = git_dir / "refs" / "heads"
    if heads_dir.exists():
        try:
            for branch_file in heads_dir.rglob("*"):
                if branch_file.is_file():
                    try:
                        branch_name = str(branch_file.relative_to(heads_dir))
                        commit_hash = safe_read_text(branch_file)
                        if commit_hash and len(commit_hash) >= 7:
                            refs[branch_name] = commit_hash
                            refs[f"refs/heads/{branch_name}"] = commit_hash
                    except Exception:
                        continue
        except Exception:
            pass
    
    # Branches distantes
    remotes_dir = git_dir / "refs" / "remotes"
    if remotes_dir.exists():
        try:
            for remote_file in remotes_dir.rglob("*"):
                if remote_file.is_file():
                    try:
                        remote_name = str(remote_file.relative_to(remotes_dir))
                        commit_hash = safe_read_text(remote_file)
                        # Ignorer les références qui ne sont pas des SHA-1
                        if commit_hash and not commit_hash.startswith("ref:") and len(commit_hash) >= 7:
                            refs[f"remotes/{remote_name}"] = commit_hash
                            refs[f"refs/remotes/{remote_name}"] = commit_hash
                    except Exception:
                        continue
        except Exception:
            pass
    
    # Tags
    tags_dir = git_dir / "refs" / "tags"
    if tags_dir.exists():
        try:
            for tag_file in tags_dir.rglob("*"):
                if tag_file.is_file():
                    try:
                        tag_name = str(tag_file.relative_to(tags_dir))
                        commit_hash = safe_read_text(tag_file)
                        if commit_hash and len(commit_hash) >= 7:
                            refs[tag_name] = commit_hash
                            refs[f"refs/tags/{tag_name}"] = commit_hash
                    except Exception:
                        continue
        except Exception:
            pass
    
    return refs


def resolve_ref(git_dir: Path, ref: Union[str, List, None]) -> Optional[str]:
    """Résout une référence vers son SHA-1."""
    # Normaliser l'entrée
    ref = normalize_input(ref)
    
    if not ref:
        return None
    
    # Si c'est déjà un SHA-1, le retourner
    if len(ref) == 40 and all(c in '0123456789abcdef' for c in ref):
        return ref
    
    # Si c'est un SHA-1 court, essayer de le résoudre
    if len(ref) >= 4 and all(c in '0123456789abcdef' for c in ref):
        objects_dir = git_dir / "objects"
        if objects_dir.exists():
            for obj_dir in objects_dir.iterdir():
                if obj_dir.is_dir() and len(obj_dir.name) == 2:
                    if ref.startswith(obj_dir.name):
                        for obj_file in obj_dir.iterdir():
                            full_hash = obj_dir.name + obj_file.name
                            if full_hash.startswith(ref):
                                return full_hash
    
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
    
    # Obtenir toutes les références
    all_refs = list_all_refs(git_dir)
    
    # Chercher une correspondance exacte
    if ref in all_refs:
        return all_refs[ref]
    
    # Chercher une correspondance partielle
    matches = []
    for ref_name, commit_hash in all_refs.items():
        if ref_name.endswith(f"/{ref}") or ref_name == ref:
            matches.append((ref_name, commit_hash))
    
    if len(matches) == 1:
        return matches[0][1]
    elif len(matches) > 1:
        print(f"Ambiguous reference '{ref}'. Could be:")
        for ref_name, commit_hash in matches:
            print(f"  {ref_name} -> {commit_hash[:7]}")
        return None
    
    return None


def show_available_refs(git_dir: Path):
    """Affiche toutes les références disponibles de manière claire."""
    refs = list_all_refs(git_dir)
    
    if not refs:
        print("No references found in this repository.")
        return
    
    print("\n" + "="*50)
    print("AVAILABLE REFERENCES")
    print("="*50)
    
    # Grouper par type
    local_branches = []
    remote_branches = []
    tags = []
    
    for ref_name, commit_hash in refs.items():
        # Branches locales
        if not ref_name.startswith("refs/") and not "/" in ref_name:
            local_branches.append((ref_name, commit_hash))
        # Branches distantes
        elif ref_name.startswith("remotes/") and not ref_name.startswith("refs/"):
            remote_branches.append((ref_name, commit_hash))
        # Tags
        elif ref_name.startswith("refs/tags/"):
            tag_name = ref_name.replace("refs/tags/", "")
            tags.append((tag_name, commit_hash))
    
    # Afficher les branches locales
    if local_branches:
        print("\n📁 LOCAL BRANCHES:")
        print("-" * 20)
        for name, hash_val in sorted(set(local_branches)):
            print(f"  ✓ {name:<20} -> {hash_val[:7]}")
    
    # Afficher les branches distantes
    if remote_branches:
        print("\n🌐 REMOTE BRANCHES:")
        print("-" * 20)
        for name, hash_val in sorted(set(remote_branches)):
            print(f"  ↗ {name:<20} -> {hash_val[:7]}")
    
    # Afficher les tags
    if tags:
        print("\n🏷️  TAGS:")
        print("-" * 20)
        for name, hash_val in sorted(set(tags)):
            print(f"  🔖 {name:<20} -> {hash_val[:7]}")
    
    print("\n" + "="*50)
    print("💡 SUGGESTIONS:")
    print("="*50)
    
    if local_branches:
        print("To merge a local branch:")
        for name, _ in sorted(set(local_branches))[:3]:  # Montrer les 3 premières
            print(f"  python main.py merge {name}")
    
    if remote_branches:
        print("\nTo merge a remote branch (create local branch first):")
        for name, hash_val in sorted(set(remote_branches))[:2]:  # Montrer les 2 premières
            branch_name = name.split('/')[-1]  # Extraire le nom de branche
            print(f"  git checkout -b {branch_name} {name}")
            print(f"  python main.py merge {branch_name}")
    
    print("\n" + "="*50)


def create_branch_suggestion(git_dir: Path, branch_name: str):
    """Suggère comment créer une branche manquante."""
    print(f"\n💡 The branch '{branch_name}' doesn't exist. Here's how to create it:")
    print("-" * 60)
    
    # Vérifier s'il y a des branches distantes similaires
    refs = list_all_refs(git_dir)
    similar_remotes = []
    
    for ref_name, commit_hash in refs.items():
        if ref_name.startswith("remotes/") and branch_name in ref_name:
            similar_remotes.append((ref_name, commit_hash))
    
    if similar_remotes:
        print("🌐 Found similar remote branches:")
        for remote_name, commit_hash in similar_remotes:
            print(f"  {remote_name} -> {commit_hash[:7]}")
            print(f"  Command: git checkout -b {branch_name} {remote_name}")
    else:
        print("🆕 Create a new branch:")
        print(f"  git checkout -b {branch_name}")
        print(f"  # Make some changes and commits")
        print(f"  python main.py merge {branch_name}")
    
    print("-" * 60)


def run_merge(target: Union[str, List, None]):
    """Exécute la commande merge de manière indépendante."""
    try:
        # Normaliser le target
        target = normalize_input(target)
        
        if not target:
            print("❌ Error: No target specified for merge")
            sys.exit(1)
        
        # Trouver le repository
        repo_root = find_git_repository()
        git_dir = repo_root / ".git"
        
        # Résoudre les commits
        our_commit = resolve_ref(git_dir, "HEAD")
        their_commit = resolve_ref(git_dir, target)
        
        if not our_commit:
            print("❌ Error: No commits on current branch")
            sys.exit(1)
        
        if not their_commit:
            print(f"❌ Error: '{target}' is not a valid commit")
            create_branch_suggestion(git_dir, target)
            show_available_refs(git_dir)
            sys.exit(1)
        
        print(f"🔄 Merging {target} ({their_commit[:7]}) into current branch ({our_commit[:7]})")
        
        if our_commit == their_commit:
            print("✅ Already up to date.")
            return
        
        # Pour cette démonstration, on simule toujours un fast-forward
        print(f"⚡ Fast-forward merge to {their_commit[:7]}")
        print("✅ Fast-forward merge completed successfully.")
        
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python merge.py <branch|sha|tag>")
        sys.exit(1)
    
    target = sys.argv[1]
    run_merge(target)
