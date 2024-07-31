# ChiaLogMonitor

**Description**  
ChiaLogMonitor est une application Tkinter pour surveiller et visualiser les logs de Chia.  
Elle lit les fichiers de log, extrait des informations spécifiques, et affiche des graphiques et des statistiques en temps réel.



## Méthodes Principales

- **Initialisation de l'application Tkinter (`__init__`)**  
  Initialise l'interface utilisateur.  
  Crée des éléments comme les boutons, les zones de texte et les graphiques.  
  Configure les couleurs et les polices.

- **Lecture du fichier de log (`read_log_file`)**  
  Lit le fichier de log ligne par ligne.  
  Met à jour la barre de progression.  
  Stocke les données lues dans `log_data`.  
  Utilise des fonctions de parsing pour extraire des informations spécifiques à partir des lignes du log.

- **Lecture de nouvelles lignes (`read_new_lines`)**  
  Lit les nouvelles lignes ajoutées au fichier de log depuis la dernière lecture.  
  Met à jour l'interface utilisateur et les graphiques.

- **Choisir un fichier de log (`choose_log_file`)**  
  Permet à l'utilisateur de sélectionner un fichier de log via une boîte de dialogue de sélection de fichiers.

- **Charger un fichier de log (`load_log_file`)**  
  Vérifie si un fichier de log par défaut existe, sinon demande à l'utilisateur de sélectionner un fichier.

- **Mise à jour du fichier de log (`update_log_file`)**  
  Appelle périodiquement `read_new_lines` pour vérifier les nouvelles lignes dans le fichier de log.  
  Met à jour l'interface utilisateur.

- **Démarrer la surveillance du fichier (`start_monitoring`)**  
  Initialise la surveillance du fichier en enregistrant la taille actuelle du fichier.  
  Démarre une boucle de mise à jour périodique.

- **Démarrer la lecture du fichier de log (`start_read_log_file`)**  
  Lance la lecture du fichier de log dans un thread séparé pour ne pas bloquer l'interface utilisateur.  
  Démarre la surveillance des changements du fichier.

- **Mise à jour périodique de l'interface (`update_periodically`)**  
  Appelle `update_ui` périodiquement pour rafraîchir l'interface utilisateur.

- **Mise à jour de l'interface utilisateur (`update_ui`)**  
  Met à jour les éléments de l'interface utilisateur.  
  Affiche le résumé et les statistiques des logs ou un message de chargement.

- **Tracer les données (`plot_data`)**  
  Filtre et traite les données du log pour les graphiques.  
  Appelle des méthodes pour tracer ces données.

- **Graphiques de toutes les preuves (`all_proof_graphs`)**  
  Génère un graphique de dispersion pour les temps de toutes les preuves trouvées dans les dernières heures.  
  Utilise différentes couleurs pour les temps <= 8 secondes et > 8 secondes.

- **Graphiques des preuves trouvées (`found_proof_graphs`)**  
  Génère un graphique de dispersion pour les temps des preuves trouvées dans les dernières heures.  
  Utilise des couleurs spécifiques pour les temps <= 8 secondes et > 8 secondes.

- **Centrage de la fenêtre (`center_window`)**  
  Centre la fenêtre de l'application sur l'écran.

- **Fermeture de l'application (`close_app`)**  
  Ferme proprement l'application Tkinter.

- **Fonction principale (`main`)**  
  Crée une instance de l'application `LogMonitorApp`.  
  Lance la boucle principale de Tkinter.
<br><br><br>
## Installation et Construction

**Prérequis**  
- Python 3.6 ou supérieur  
- CMake 3.5 ou supérieur  
- GCC (MinGW pour Windows)  
- PyInstaller
<br><br>
**Build sur Linux**  
1. Cloner le dépôt Git :  
   ```bash
   git clone https://github.com/Emzime/Chia_Log_Monitor.git
2. Se déplacer dans le répertoire du projet :
   ```bash
   cd Chia_Log_Monitor       
3. Créer un environnement virtuel :
   ```bash
   python -m venv venv       
4. Activer l'environnement virtuel :
   ```bash
   source venv/bin/activate       
5. Construction :
   ```bash
   python build.sh
<br><br>
**Build sur Windows**  
1. Cloner le dépôt Git :  
   ```bash
   git clone https://github.com/Emzime/Chia_Log_Monitor.git       
2. Se déplacer dans le répertoire du projet :
   ```bash
   cd Chia_Log_Monitor
3. Créer et activer un environnement virtuel :
   ```bash
   python -m venv venv .\venv\Scripts\activate
4. Construction :
   ```bash
   python build.bat
