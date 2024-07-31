@echo off
setlocal

REM Changer l'encodage de la console à UTF-8
chcp 65001 >nul

REM Définir le répertoire de travail actuel
set "PROJECT_DIR=%CD%"

REM Installer les dépendances
echo Installation des dépendances Python...
pip install -r "%PROJECT_DIR%\requirements.txt" || (echo Échec de l'installation des dépendances & pause & exit /b 1)

REM Créer le répertoire de build
if not exist build mkdir build
cd build || (echo Impossible de créer le répertoire de build & pause & exit /b 1)

REM Exécuter CMake pour configurer le projet
cmake .. || (echo Échec de l'exécution de CMake & pause & exit /b 1)

REM Construire l'exécutable autonome
echo Construction de l'exécutable autonome...
cmake --build . --target ChiaLogMonitorAutonome || (echo Échec de la construction de l'exécutable autonome & pause & exit /b 1)

REM Construire l'exécutable non autonome
echo Construction de l'exécutable non autonome...
cmake --build . --target ChiaLogMonitorNonAutonome || (echo Échec de la construction de l'exécutable non autonome & pause & exit /b 1)

echo Build terminé.
pause
