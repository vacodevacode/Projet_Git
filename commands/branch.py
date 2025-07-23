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
    branches_dir = os.path.join(".mygit", "refs", "heads")
    if not args:
        # Afficher la liste des branches avec un astérisque sur la courante
        branches = [f for f in os.listdir(branches_dir) if os.path.isfile(os.path.join(branches_dir, f)) and not f.endswith('.remote')]
        current_branch = get_current_branch()
        for branch in branches:
            if branch == current_branch:
                print(f"* {branch}")
            else:
                print(f"  {branch}")
        return

    branch = args[0]
    branch_ref = os.path.join(branches_dir, branch)
    remote_ref = os.path.join(branches_dir, branch + ".remote")
    if not os.path.exists(branch_ref):
        with open(branch_ref, "w") as f:
            f.write("")
        with open(remote_ref, "w") as f:
            f.write("")
        print(f"Branche '{branch}' créée.")
    else:
        print(f"La branche '{branch}' existe déjà.")