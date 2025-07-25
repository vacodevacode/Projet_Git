# My Github

- Ce projet a pour but de recréer les fonctionnalités principales de Git en Python. Nous avons donc recoder les commandes de Git.

## 📁 Structure du projet

- **main.py** : Point d’entrée du projet, gère le parsing des commandes.
- **commands/** : Dossier contenant les implémentations des commandes Git (commit, log, status, etc.).
- **.mygit/** : Dossier interne pour stocker les objets, l’index, les références de branches, etc.
- **app.py** : Serveur Flask pour l’explorateur web du dépôt.
- **README.md** : Ce fichier d’explications.

## ⚙️ Pré-requis

- Python 3.x
- VS Code, ou n’importe quel terminal avec Python
- pip install -r requirement.txt

/!\ Dans l'interface Web , il y a eu un petit soucis pour la visualisation des fichiers contenue dans un dossier ( N'y prêtez pas attention je vous pris )
Le test d'integration est effectué avec intégration.yml ( Voir Github Actions )

## 🚀 Commandes disponibles

- **my_git_add** : Ajouter des fichiers/dossiers à l'index (ajouter un README.md il se met au bon endroit )  
  ```bash
  python main.py my_git_add <fichier|dossier>
  ```
- **my_git_init** : Initialiser un nouveau dépôt  
  ```bash
  python main.py my_git_init
  ```
- **push** : Pousser la branche courante  
  ```bash
  python main.py push
  ```
- **reset** : Réinitialiser l'index comme le dernier commit  
  ```bash
  python main.py reset
  ```
- **status** : Afficher le statut du dépôt  
  ```bash
  python main.py status
  ```
- **write_tree** : Écrire l'arbre à partir de l'index  
  ```bash
  python main.py write_tree
  ```
- **branch** : Voir ou créer des branches  
  ```bash
  python main.py branch [nom_branche]
  ```
- **checkout** : Changer de branche et restaurer l'état du projet  
  ```bash
  python main.py checkout <nom_branche>
  ```
- **commit** : Enregistrer les modifications indexées  
  ```bash
  python main.py commit -m "Message du commit"
  ```
- **commit_tree** : Créer un commit à partir d'un tree  
  ```bash
  python main.py commit_tree <tree_sha> -m "Message" [-p <parent_sha>]
  ```
- **git_cat_file** : Afficher le contenu ou le type d'un objet  
  ```bash
  python main.py cat-file -p|-t <sha1>
  ```
- **log** : Afficher l'historique des commits  
  ```bash
  python main.py log
  ```
- **merge** : Fusionner une branche ou un commit  
  ```bash
  python main.py merge <branche|sha|tag>
  ```
---

## 💻 Interface Web

Lance le serveur Flask pour explorer le dépôt dans le navigateur :
```bash
python app.py
```
Accède ensuite à [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📝 Auteurs

- Projet réalisé par : 

- M'FOUMOUNE Gabrielle,
- OUARDI Ahmed-amine,
- PILLAH Niali henri guy-harvyn
- MABANZA Danali

---
