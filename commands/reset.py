import os
import zlib

def read_object(sha1, type_):
    obj_dir = os.path.join(".mygit", "objects", sha1[:2])
    obj_path = os.path.join(obj_dir, sha1[2:])
    with open(obj_path, "rb") as f:
        data = zlib.decompress(f.read())
    header_end = data.find(b'\0')
    header = data[:header_end].decode()
    assert header.startswith(type_)
    return data[header_end+1:]

def get_last_commit_hash():
    head_path = os.path.join(".mygit", "HEAD")
    if os.path.exists(head_path):
        with open(head_path) as f:
            ref = f.read().strip()
            if ref.startswith("ref:"):
                branch = ref.split("/")[-1]
                branch_path = os.path.join(".mygit", "refs", "heads", branch)
                if os.path.exists(branch_path):
                    with open(branch_path) as bf:
                        return bf.read().strip()
    return None

def get_tree_from_commit(commit_hash):
    if not commit_hash:
        return None
    commit_data = read_object(commit_hash, "commit").decode()
    for line in commit_data.splitlines():
        if line.startswith("Tree:"):
            return line.split(":", 1)[1].strip()
    return None

def collect_tree(tree_hash, base_path=""):
    tree_data = read_object(tree_hash, "tree")
    files = []
    for line in tree_data.decode().splitlines():
        if line.startswith("blob "):
            _, _, filename = line.split(" ", 2)
            path = f"{base_path}/{filename}" if base_path else filename
            path = path.replace("\\", "/")
            files.append(path)
        elif line.startswith("tree "):
            _, sub_tree_hash, dirname = line.split(" ", 2)
            folder_path = f"{base_path}/{dirname}" if base_path else dirname
            folder_path = folder_path.replace("\\", "/")
            files.extend(collect_tree(sub_tree_hash, folder_path))
    return files

def run(args):
    # 1. Récupérer le dernier commit
    commit_hash = get_last_commit_hash()
    if not commit_hash:
        print("Aucun commit trouvé.")
        return

    # 2. Récupérer le tree du commit
    tree_hash = get_tree_from_commit(commit_hash)
    if not tree_hash:
        print("Aucun tree trouvé dans le commit.")
        return

    # 3. Récupérer tous les fichiers du tree
    files = collect_tree(tree_hash)

    # 4. Réécrire l'index avec ces fichiers
    index_file = os.path.join(".mygit", "index")
    with open(index_file, "w", encoding="utf-8") as f:
        for file in files:
            f.write(file + "\n")
    print("Index synchronisé avec le dernier commit (reset comme git).")