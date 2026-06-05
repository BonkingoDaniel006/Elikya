



# Elikya - Plateforme E-commerce / Gestion de Boutique

Elikya est une application web développée avec Flask permettant aux utilisateurs de s'inscrire, de créer une boutique et de gérer leurs informations. Le projet utilise une architecture modulaire avec des Blueprints et une base de données MySQL.

## 🚀 Technologies utilisées

- **Backend :** Python 3.12+, Flask
- **Authentification :** Flask-Login
- **Sécurité :** Flask-Bcrypt (hachage des mots de passe)
- **Base de données :** MySQL (via `mysql-connector-python`)
- **Configuration :** Python-dotenv

## 📂 Structure du Projet

```text
elikya/
├── auth/
│   ├── models.py      # Modèle User et logique d'accès DB
│   └── routes.py      # Routes d'inscription, connexion et déconnexion
├── static/
│   └── dashboard.css  # Styles du tableau de bord et des composants
├── templates/         # Fichiers HTML (inscription, connexion, index)
├── app.py             # Point d'entrée de l'application (Factory Pattern)
├── config.py          # Configuration des variables d'environnement
├── ext.py             # Initialisation des extensions Flask
└── .env               # Variables confidentielles (non inclus au dépôt)
```

## 🛠️ Installation et Configuration

### 1. Cloner le projet
```bash
git clone <url-du-depot>
cd elikya
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install flask flask-login flask-bcrypt mysql-connector-python python-dotenv
```

### 4. Configurer la base de données
Créez une base de données MySQL et exécutez le script suivant pour créer la table des utilisateurs :

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prenom VARCHAR(100),
    nom VARCHAR(100),
    postnom VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    naissance DATE,
    password VARCHAR(255) NOT NULL,
    description TEXT,
    adresse TEXT,
    nom_boutique VARCHAR(150)
);
```

### 5. Variables d'environnement
Créez un fichier `.env` à la racine du projet :

```env
SECRET_KEY=votre_cle_secrete
DB_HOST=localhost
DB_USER=votre_utilisateur
DB_PASSWORD=votre_mot_de_passe
DB_NAME=votre_nom_db
```

## 🏃‍♂️ Lancement

Pour démarrer l'application en mode debug :
```bash
python app.py
```
L'application sera accessible sur `http://127.0.0.1:5000`.

## 📋 Fonctionnalités actuelles

- **Inscription :** Formulaire complet incluant les détails de la boutique.
- **Connexion / Déconnexion :** Gestion des sessions sécurisée.
- **Dashboard :** Interface utilisateur protégée par authentification.
- **Sécurité :** Protection des routes via `@login_required` et hachage des mots de passe.

## 📝 Notes pour la suite du développement

1. **Initialisation DB :** La fonction `init_db()` dans `app.py` est prête mais ne contient pas encore les requêtes de création de table automatique (`CREATE TABLE IF NOT EXISTS`).
2. **Modèles :** Le modèle `User` dans `auth/models.py` ne récupère actuellement que l'`id`, l'`email` et le `password`. Il faudra l'étendre pour inclure les autres champs (nom, boutique, etc.) si nécessaire dans l'objet `current_user`.
3. **Templates :** S'assurer que les fichiers `inscription.html`, `connexion.html` et `index.html` sont présents dans le dossier `templates/`.

---
*Documentation générée pour faciliter la reprise du projet.*
```

En tant que ton assistant, j'ai structuré ce README pour qu'il soit directement utilisable. J'ai ajouté une section sur la structure SQL nécessaire car elle est implicite dans tes routes d'inscription mais indispensable pour quelqu'un qui installe le projet.

Note aussi que j'ai précisé dans les "Notes pour la suite" que ton fichier `app.py` possède une fonction `init_db()` qui est actuellement vide (elle ne crée pas encore les tables), ce qui est un bon point de départ pour la prochaine étape.

<!--
[PROMPT_SUGGESTION]Peux-tu m'aider à compléter la fonction init_db dans app.py pour créer automatiquement la table users ?[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]Comment puis-je modifier le modèle User pour qu'il contienne aussi le nom de la boutique ?[/PROMPT_SUGGESTION]
