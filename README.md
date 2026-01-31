# Projet_Webscraping_Api

## Auteurs :
- FOGUE FEUSSI Franck Jorel
- VIDAL Victoria
- AIT SAID Melina 

## Objectif du projet
Le but du projet est de concevoir un système capable de générer automatiquement des
propositions de réponses personnalisées aux avis clients collectés sur différentes plate
formes en ligne.

## Installation du projet
1. **Prérequis**
- Python >= 3.12
- Git Bash (ou terminal équivalent)

2. **Cloner le projet**
```bash
git clone https://github.com/JOREL531/Projet_Webscraping_Api.git
cd Projet_Webscraping_Api
```

3. **Créer un environnement virtuel**
- installer virtualenv (*si vous ne l'avez pas*)
```bash
pip install virtualenv
``` 

- Créer un environnement virtuel
```bash
virtualenv .venv
```

- Activer votre environnement virtuel
Sous **Windows** :
```bash
source .venv/Scripts/activate
```

Sous **Linux / MacOS** :
```bash
source .venv/bin/activate
```

4. **Installer les dépendances**
(si vous n'avez pas poetry veuillez à l'installer au préalable)
```bash
poetry install
```

5. **Lancer l'API**
```bash
uvicorn functions.API.main:app
```
- Une fois le serveur lancé, ouvrez votre navigateur et allez sur :
```bash
http://127.0.0.1:8000/docs
```

6. **EXTRACTION DES REVIEWS : AMAZON**

Pour extraire les reviews sur Amazon, veuillez suivre les étapes : 
- Insérer votre user-agent dans la variable **user_agent** du notebook scraping.ipynb, puis exécuter le code. la fonction **save_cookies** va vous rediriger vers la page de connexion Amazon. Remplissez y vos identifiants de connexion Amazon, puis **retourner dans votre vscode**, **dans la barre des input** et **appuyer sur ENTREE(clavier)**. Le fait d'appuyer sur ENTREE indique au code que vous avez fini le remplissage de vos identifiants. Par la suite un fichier **cookies.pkl** sera automatiquement crée dans l'arborescence de vôtre projet; il contient vos cookies de connexion. L'objectif est donc d'utiliser ces cookies chaque fois qu'on se connecte à Amazon. **Vous n'aurez à faire cette étape qu'une seule fois**

- Une fois la première étape terminée, il vous suffit de lancer le code d'extraction (**Sans avoir réalisé cette étape, l'API ne fonctionnera pas pour AMAZON**)