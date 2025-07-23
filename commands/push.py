import os

def get_current_branch():
    head_path = os.path.join(".mygit", "HEAD")
    if os.path.exists(head_path):
        with open(head_path) as f:
            line = f.read().strip()
            if line.startswith("ref:"):
                return line.split("/")[-1]
    return "main"

def run(args):
    branch = get_current_branch()
    local_ref = os.path.join(".mygit", "refs", "heads", branch)
    remote_ref = os.path.join(".mygit", "refs", "heads", branch + ".remote")
    if not os.path.exists(local_ref):
        print("Aucun commit local à pousser.")
        return
    with open(local_ref, "r", encoding="utf-8") as f:
        commit_hash = f.read().strip()
    if not commit_hash:
        print("Aucun commit local à pousser.")
        return
    with open(remote_ref, "w", encoding="utf-8") as f:
        f.write(commit_hash)
    print(f"Branche '{branch}' poussée (push) !")

    # Vider l'index après le push
    index_file = os.path.join(".mygit", "index")
    if os.path.exists(index_file):
        open(index_file, "w", encoding="utf-8").close()

