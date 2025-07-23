import os

def run(args):
    index_file = os.path.join(".mygit", "index")
    if os.path.exists(index_file):
        open(index_file, "w").close()
        print("Index vidé (tous les fichiers retirés de l'index).")
    else:
        print("Aucun fichier dans l'index.")