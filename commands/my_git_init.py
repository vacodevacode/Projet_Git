import os

def run(args):
    if not os.path.exists(".mygit"):
        os.makedirs(".mygit")
        print("Youpiii c'st bon j'ai crée mon dossier .mygit")

    objects_dir = os.path.join(".mygit", "objects")
    if not os.path.exists(objects_dir):
        os.makedirs(objects_dir, exist_ok=True)
        print("Yeees j'ai crée le dossier .mygit/objects")
    
    refs_heads_dir = os.path.join(".mygit", "refs", "heads")
    os.makedirs(refs_heads_dir, exist_ok=True)
    print("Création du dosssier .mygit/refs/heads")
    
    main_ref = os.path.join(refs_heads_dir, "main")
    if not os.path.exists(main_ref):
        with open(main_ref, "w") as f:
            f.write("")
        print("C'est bon je crée la branche 'main' elle est initialisée")

    main_remote_ref = os.path.join(refs_heads_dir, "main.remote")
    if not os.path.exists(main_remote_ref):
        with open(main_remote_ref, "w") as f:
            f.write("")
        print("C'est bon j'ai créé mon main.remote")        

    head_path = os.path.join(".mygit", "HEAD")
    with open(head_path, "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Mon HEAD pointe bien sur main")

    index_path = os.path.join(".mygit", "index")
    if not os.path.exists(index_path):
        open(index_path, "w").close()
        print("Youpiiii j'ai intilisé l'index (.mon_git/index)")
    print("Youpiii j'ai initalisé mon dépôt !")