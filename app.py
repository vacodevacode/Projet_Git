from flask import Flask, render_template, redirect, url_for, abort
import os
import markdown
import zlib

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

def get_current_branch():
    head_path = os.path.join(".mygit", "HEAD")
    if os.path.exists(head_path):
        with open(head_path) as f:
            line = f.read().strip()
            if line.startswith("ref:"):
                return line.split("/")[-1]
    return "main"

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

def get_last_pushed_commit_hash(branch):
    ref_path = os.path.join(".mygit", "refs", "heads", branch + ".remote")
    if not os.path.exists(ref_path):
        return None
    with open(ref_path) as f:
        return f.read().strip() or None

def get_tree_hash_from_commit(commit_hash):
    commit_data = read_object(commit_hash, "commit")
    if not commit_data:
        return None
    lines = commit_data.decode().splitlines()
    for line in lines:
        if line.startswith("tree "):
            return line.split(" ", 1)[1].strip()
    return None

def collect_tree(tree_hash, base_path=""):
    """Récupère tous les fichiers et dossiers du tree récursivement."""
    tree_data = read_object(tree_hash, "tree")
    files = []
    folders = []
    for line in tree_data.decode().splitlines():
        if line.startswith("blob "):
            _, _, filename = line.split(" ", 2)
            path = os.path.join(base_path, filename) if base_path else filename
            path = path.replace("\\", "/")  
            files.append(path)
        elif line.startswith("tree "):
            _, sub_tree_hash, dirname = line.split(" ", 2)
            folder_path = os.path.join(base_path, dirname) if base_path else dirname
            folder_path = folder_path.replace("\\", "/")  
            folders.append(folder_path)
            sub_files, sub_folders = collect_tree(sub_tree_hash, folder_path)
            files.extend(sub_files)
            folders.extend(sub_folders)
    return files, folders

def get_last_pushed_commit_files(branch):
    commit_hash = get_last_pushed_commit_hash(branch)
    if not commit_hash:
        return []
    tree_hash = get_tree_hash_from_commit(commit_hash)
    if not tree_hash:
        return []
    files, _ = collect_tree(tree_hash)
    return files

def get_last_pushed_commit_tree(branch):
    commit_hash = get_last_pushed_commit_hash(branch)
    if not commit_hash:
        return None
    tree_hash = get_tree_hash_from_commit(commit_hash)
    return tree_hash

def get_tree_listing(tree_hash, subpath=""):
    """Retourne les dossiers et fichiers à un niveau donné du tree."""
    tree_data = read_object(tree_hash, "tree")
    files = []
    folders = []
    for line in tree_data.decode().splitlines():
        if line.startswith("blob "):
            _, _, filename = line.split(" ", 2)
            files.append(filename)
        elif line.startswith("tree "):
            _, sub_tree_hash, dirname = line.split(" ", 2)
            folders.append(dirname)
    return files, folders

def build_tree_structure(tree_hash, base_path=""):
    tree_data = read_object(tree_hash, "tree")
    tree = []
    for line in tree_data.decode().splitlines():
        if line.startswith("blob "):
            _, _, filename = line.split(" ", 2)
            tree.append({"type": "file", "name": filename, "path": os.path.join(base_path, filename) if base_path else filename})
        elif line.startswith("tree "):
            _, sub_tree_hash, dirname = line.split(" ", 2)
            subtree = build_tree_structure(sub_tree_hash, os.path.join(base_path, dirname) if base_path else dirname)
            tree.append({"type": "folder", "name": dirname, "path": os.path.join(base_path, dirname) if base_path else dirname, "children": subtree})
    return tree

@app.route("/")
@app.route("/branch/<branch>")
def depot(branch=None):
    current_branch = branch or get_current_branch()
    files = get_last_pushed_commit_files(current_branch)

    # Liste des branches (ignore les .remote)
    branches_dir = os.path.join(".mygit", "refs", "heads")
    branches = []
    if os.path.exists(branches_dir):
        branches = [f for f in os.listdir(branches_dir)
                    if os.path.isfile(os.path.join(branches_dir, f)) and not f.endswith('.remote')]
    if "main" not in branches:
        branches.append("main")

    index = []
    index_path = os.path.join(".mygit", "index")
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = [line.strip() for line in f if line.strip()]

    # Associer chaque fichier à son message de commit
    file_commits = {}
    if os.path.exists("commits.txt"):
        with open("commits.txt", encoding="utf-8") as f:
            lines = f.readlines()
        current_message = ""
        current_author = ""
        current_date = ""
        current_files = []
        current_folders = []
        commit_hash = None
        for line in lines:
            if line.startswith("commit "):
                commit_hash = line.split()[1].strip()
            elif line.startswith("Message:"):
                current_message = line[len("Message:"):].strip()
            elif line.startswith("Auteur:"):
                current_author = line[len("Auteur:"):].strip()
            elif line.startswith("Date:"):
                current_date = line[len("Date:"):].strip()
            elif line.strip().startswith("- "):
                parts = line.strip()[2:].split()
                if len(parts) == 3 and parts[0] == "blob":
                    filename = parts[2]
                    current_files.append(filename)
                elif len(parts) == 3 and parts[0] == "tree":
                    foldername = parts[2]
                    current_folders.append(foldername)
            elif line.strip() == "":
                for file in current_files:
                    file_commits[file] = {
                        "author": current_author,
                        "message": current_message,
                        "date": current_date,
                        "hash": commit_hash
                    }
                for folder in current_folders:
                    file_commits[folder] = {
                        "author": current_author,
                        "message": current_message,
                        "date": current_date,
                        "hash": commit_hash
                    }
                current_files = []
                current_folders = []

    # README
    readme_content = None
    readme_file = None
    for f in files:
        if f.lower() == "readme.md":
            readme_file = f
            break
    if readme_file and os.path.exists(readme_file):
        with open(readme_file, encoding="utf-8") as f:
            md = f.read()
            readme_content = markdown.markdown(md)

    return render_template(
        "depot.html",
        files=files,
        branches=branches,
        current_branch=current_branch,
        index=index,
        file_commits=file_commits,
        readme_content=readme_content
    )

@app.route("/tree/<branch>/", defaults={"subpath": ""})
@app.route("/tree/<branch>/<path:subpath>")
def explorer(branch, subpath):
    subpath = subpath.replace("\\", "/")
    tree_hash = get_last_pushed_commit_tree(branch)
    if not tree_hash:
        abort(404)
    tree_structure = build_tree_structure(tree_hash)
    current_tree_hash = tree_hash
    selected_file_content = None
    selected_file_name = None

    # Ajout branches pour le menu déroulant
    branches_dir = os.path.join(".mygit", "refs", "heads")
    branches = []
    if os.path.exists(branches_dir):
        branches = [f for f in os.listdir(branches_dir)
                    if os.path.isfile(os.path.join(branches_dir, f)) and not f.endswith('.remote')]
    if "main" not in branches:
        branches.append("main")

    # Afficher les messages/dates
    file_commits = {}
    folder_commits = {}
    if os.path.exists("commits.txt"):
        with open("commits.txt", encoding="utf-8") as f:
            lines = f.readlines()
        current_message = ""
        current_author = ""
        current_date = ""
        current_files = []
        current_folders = []
        commit_hash = None
        for line in lines:
            if line.startswith("commit "):
                commit_hash = line.split()[1].strip()
            elif line.startswith("Message:"):
                current_message = line[len("Message:"):].strip()
            elif line.startswith("Author:"):
                current_author = line[len("Author:"):].strip()
            elif line.startswith("Date:"):
                current_date = line[len("Date:"):].strip()
            elif line.strip().startswith("- "):
                parts = line.strip()[2:].split()
                if len(parts) == 3 and parts[0] == "blob":
                    filename = parts[2]
                    current_files.append(filename)
                elif len(parts) == 3 and parts[0] == "tree":
                    foldername = parts[2]
                    current_folders.append(foldername)
            elif line.strip() == "":
                for file in current_files:
                    file_commits[file] = {
                        "author": current_author,
                        "message": current_message,
                        "date": current_date,
                        "hash": commit_hash
                    }
                for folder in current_folders:
                    folder_commits[folder] = {
                        "author": current_author,
                        "message": current_message,
                        "date": current_date,
                        "hash": commit_hash
                    }
                current_files = []
                current_folders = []

    # Si subpath est un fichier, on affiche son contenu
    if subpath:
        parts = subpath.split("/")
        # On tente d'aller jusqu'au fichier
        for part in parts[:-1]:
            tree_data = read_object(current_tree_hash, "tree")
            found = False
            for line in tree_data.decode().splitlines():
                if line.startswith("tree "):
                    _, sub_tree_hash, dirname = line.split(" ", 2)
                    if dirname == part:
                        current_tree_hash = sub_tree_hash
                        found = True
                        break
            if not found:
                abort(404)
        tree_data = read_object(current_tree_hash, "tree")
        blob_hash = None
        for line in tree_data.decode().splitlines():
            if line.startswith("blob "):
                _, bhash, fname = line.split(" ", 2)
                if fname == parts[-1]:
                    blob_hash = bhash
                    break
        if blob_hash:
            blob_data = read_object(blob_hash, "blob")
            selected_file_name = parts[-1]
            if selected_file_name.lower().endswith('.md'):
                selected_file_content = markdown.markdown(blob_data.decode(errors="replace"))
            else:
                selected_file_content = blob_data.decode(errors="replace")
            # Pour l'affichage, on considère le dossier parent
            subpath = "/".join(parts[:-1])
            # On affiche le contenu du dossier parent + le fichier sélectionné
    # Liste des fichiers/dossiers du dossier courant
    if subpath:
        parts = subpath.split("/") if subpath else []
        for i, part in enumerate(parts):
            tree_data = read_object(current_tree_hash, "tree")
            found = False
            for line in tree_data.decode().splitlines():
                if line.startswith("tree "):
                    _, sub_tree_hash, dirname = line.split(" ", 2)
                    if dirname == part:
                        current_tree_hash = sub_tree_hash
                        found = True
                        break
                elif line.startswith("blob ") and i == len(parts) - 1:
                    _, blob_hash, filename = line.split(" ", 2)
                    if filename == part:
                        selected_file_name = part
                        blob_data = read_object(blob_hash, "blob")
                        selected_file_content = blob_data.decode(errors="replace")
                        found = True
                        break
            if not found:
                abort(404)
    files, folders = get_tree_listing(current_tree_hash)
    selected_files = [f"{subpath}/{f}" if subpath else f for f in files]
    selected_folders = [f"{subpath}/{d}" if subpath else d for d in folders]
    return render_template(
        "explorer.html",
        branch=branch,
        branches=branches,
        tree_structure=tree_structure,
        selected_file_name=selected_file_name,
        selected_file_content=selected_file_content,
        selected_files=selected_files,
        selected_folders=selected_folders,
        subpath=subpath,
        file_commits=file_commits,
        folder_commits=folder_commits
    )

@app.route("/file_view/<branch>/<path:filepath>")
def file_view(branch, filepath):
    return redirect(url_for('explorer', branch=branch, subpath=filepath))

@app.route("/branches")
def branches_page():
    branches_dir = os.path.join(".mygit", "refs", "heads")
    branches = []
    if os.path.exists(branches_dir):
        branches = [f for f in os.listdir(branches_dir)
                    if os.path.isfile(os.path.join(branches_dir, f)) and not f.endswith('.remote')]
    if "main" not in branches:
        branches.append("main")
    current_branch = get_current_branch()
    return render_template("branches.html", branches=branches, current_branch=current_branch)

if __name__ == "__main__":
    app.run(debug=True)
    