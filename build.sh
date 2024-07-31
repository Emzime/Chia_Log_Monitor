#!/bin/bash

# Vérifier si le script est exécuté avec bash
if [ -z "$BASH_VERSION" ]; then
    echo "Ce script doit être exécuté avec bash."
    exit 1
fi

# Changer l'encodage de la console à UTF-8 (Optionnel, car généralement par défaut)
export LANG=en_US.UTF-8

# Définir le répertoire de travail actuel
PROJECT_DIR=$(pwd)

# Installer les dépendances
echo "Installation des dépendances Python..."
pip install -r "$PROJECT_DIR/requirements.txt" || { echo "Échec de l'installation des dépendances"; exit 1; }

# Créer le répertoire de build
mkdir -p build
cd build || { echo "Impossible de créer le répertoire de build"; exit 1; }

# Exécuter CMake pour configurer le projet
cmake .. || { echo "Échec de l'exécution de CMake"; exit 1; }

# Construire l'exécutable autonome
echo "Construction de l'exécutable autonome..."
cmake --build . --target ChiaLogMonitorAutonome || { echo "Échec de la construction de l'exécutable autonome"; exit 1; }

# Construire l'exécutable non autonome
echo "Construction de l'exécutable non autonome..."
cmake --build . --target ChiaLogMonitorNonAutonome || { echo "Échec de la construction de l'exécutable non autonome"; exit 1; }

echo "Build terminé."
