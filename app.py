from flask import Flask, render_template, redirect, url_for
import os
import markdown

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")


def get_current_branch():
    head_path = os.path.join(".mygit", "HEAD")
    if os.path.exists(head_path):
        with open(head_path) as f:
            line = f.read().strip()
            if line.startswith("ref:"):
                return line.split("/")[-1]
    return "main"

def get_last_pushed_commit_files(branch):
    ref_path = os.path.join(".mygit", "refs", "heads", branch + ".remote")
    if not os.path.exists(ref_path):
        return []
    with open(ref_path) as f:
        last_commit_hash = f.read().strip()
    if not last_commit_hash:
        return []
    if not os.path.exists("commits.txt"):
        return []
    with open("commits.txt", encoding="utf-8") as f:
        content = f.read()
    commits = content.strip().split("\n\n")
    for commit in reversed(commits):
        if f"Commit: {last_commit_hash}" in commit:
            files = []
            in_files = False
            for line in commit.splitlines():
                if line.strip() == "Fichiers:":
                    in_files = True
                elif in_files and line.strip().startswith("- "):
                    # ligne du type : "  - blob <hash> <filename>"
                    parts = line.strip()[2:].split()
                    if len(parts) == 3 and parts[0] == "blob":
                        files.append(parts[2])
            return files
    return []

current_branch = get_current_branch()

@app.route("/")
@app.route("/branch/<branch>")
def depot(branch=None):
    current_branch = branch or get_current_branch()
    # Affiche uniquement les fichiers du dernier commit PUSHÉ de la branche courante
    files = get_last_pushed_commit_files(current_branch)

    # Liste des branches (on ignore les .remote)
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

    file_commits = {}
    if os.path.exists("commits.txt"):
        with open("commits.txt") as f:
            lines = f.readlines()
        current_message = ""
        current_files = []
        for line in lines:
            if line.startswith("Message:"):
                current_message = line[len("Message:"):].strip()
            elif line.strip().startswith("- "):
                parts = line.strip()[2:].split()
                if len(parts) == 3 and parts[0] == "blob":
                    filename = parts[2]
                    current_files.append(filename)
            elif line.strip() == "":
                for file in current_files:
                    file_commits[file.lower()] = {"message": current_message}
                current_files = []

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