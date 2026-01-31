# Projet_Webscraping_Api

## ⚙️ Installation

- Prérequis : avoir installé `poetry` et une version compatible de Python.

- Installer les dépendances (sans installer le package racine) :

```
poetry install --no-root
```

---

## ▶️ Lancer le serveur

- Démarrer l'application avec Uvicorn :

```
poetry run uvicorn functions.API.main:app --reload
```

- Arrêter le serveur : appuyez sur `Ctrl+C` dans le terminal.

---

## 📄 Accéder à la documentation interactive (Swagger/OpenAPI)

- Une fois le serveur lancé, ouvrez votre navigateur et allez sur :

```
http://127.0.0.1:8000/docs
```

- Ou, dans la barre d'adresse, ajoutez simplement `"/docs"` à l'URL de base du serveur.

---

> ⚠️ Si `uvicorn` n'est pas trouvé, vérifiez que les dépendances sont bien installées dans l'environnement Poetry ou exécutez `poetry install` à nouveau.
