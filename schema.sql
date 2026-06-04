-- Création de la base de données
CREATE DATABASE IF NOT EXISTS elikya_db;
USE elikya_db;

-- Création de la table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prenom VARCHAR(100),
    nom VARCHAR(100),
    postnom VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    naissance DATE,
    password VARCHAR(255) NOT NULL,
    description TEXT,
    adresse TEXT,
    nom_boutique VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;