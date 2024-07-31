Description<br>
ChiaLogMonitor est une application Tkinter pour surveiller et visualiser les logs de Chia.<br>
Elle lit les fichiers de log, extrait des informations spécifiques, et affiche des graphiques et des statistiques en temps réel.<br><br><br>


Méthodes Principales
Initialisation de l'application Tkinter (__init__)<br>
    Initialise l'interface utilisateur.<br>
    Crée des éléments comme les boutons, les zones de texte et les graphiques.<br>
    Configure les couleurs et les polices.<br><br>
        
Lecture du fichier de log (read_log_file)<br>
    Lit le fichier de log ligne par ligne.<br>
    Met à jour la barre de progression.<br>
    Stocke les données lues dans log_data.<br>
    Utilise des fonctions de parsing pour extraire des informations spécifiques à partir des lignes du log.<br><br>
    
Lecture de nouvelles lignes (read_new_lines)<br>
    Lit les nouvelles lignes ajoutées au fichier de log depuis la dernière lecture.<br>
    Met à jour l'interface utilisateur et les graphiques.<br><br>

Choisir un fichier de log (choose_log_file)<br>
    Permet à l'utilisateur de sélectionner un fichier de log via une boîte de dialogue de sélection de fichiers.<br><br>

Charger un fichier de log (load_log_file)<br>
    Vérifie si un fichier de log par défaut existe, sinon demande à l'utilisateur de sélectionner un fichier.<br><br>

Mise à jour du fichier de log (update_log_file)<br>
    Appelle périodiquement read_new_lines pour vérifier les nouvelles lignes dans le fichier de log.<br>
    Met à jour l'interface utilisateur.<br><br>

Démarrer la surveillance du fichier (start_monitoring)<br>
    Initialise la surveillance du fichier en enregistrant la taille actuelle du fichier.<br>
    Démarre une boucle de mise à jour périodique.<br><br>

Démarrer la lecture du fichier de log (start_read_log_file)<br>
    Lance la lecture du fichier de log dans un thread séparé pour ne pas bloquer l'interface utilisateur.<br>
    Démarre la surveillance des changements du fichier.<br><br>

Mise à jour périodique de l'interface (update_periodically)<br>
    Appelle update_ui périodiquement pour rafraîchir l'interface utilisateur.<br><br>

Mise à jour de l'interface utilisateur (update_ui)<br>
    Met à jour les éléments de l'interface utilisateur.<br>
    Affiche le résumé et les statistiques des logs ou un message de chargement.<br><br>

Tracer les données (plot_data)<br>
    Filtre et traite les données du log pour les graphiques.<br>
    Appelle des méthodes pour tracer ces données.<br><br>

Graphiques de toutes les preuves (all_proof_graphs)<br>
    Génère un graphique de dispersion pour les temps de toutes les preuves trouvées dans les dernières heures.<br>
    Utilise différentes couleurs pour les temps <= 8 secondes et > 8 secondes.<br><br>

Graphiques des preuves trouvées (found_proof_graphs)<br>
    Génère un graphique de dispersion pour les temps des preuves trouvées dans les dernières heures.<br>
    Utilise des couleurs spécifiques pour les temps <= 8 secondes et > 8 secondes.<br><br>

Centrage de la fenêtre (center_window)<br>
    Centre la fenêtre de l'application sur l'écran.<br><br>

Fermeture de l'application (close_app)<br>
    Ferme proprement l'application Tkinter.<br><br>

Fonction principale (main)<br>
    Crée une instance de l'application LogMonitorApp.<br>
    Lance la boucle principale de Tkinter.<br><br><br>



Installation et Construction<br>
    Prérequis : <br>
        Python 3.6 ou supérieur<br>
        CMake 3.5 ou supérieur<br>
        GCC (MinGW pour Windows)<br>
        PyInstaller<br><br><br>


Build sur Linux<br>
Cloner le dépôt Git : <br>
    `git clone https://github.com/Emzime/Chia_Log_Monitor.git`<br><br>

Se déplacer dans le répertoire du projet : <br>
    `cd Chia_Log_Monitor`<br><br>
    
Créer un environnement virtuel : <br>
    `python -m venv venv`<br><br>
    
Activer l'environnement virtuel : <br>
    `source venv/bin/activate`<br><br>
    
Construction : <br>
    `python build.sh`<br><br><br>
    
    
Build sur Windows <br>
Cloner le dépôt Git : <br>
    `git clone https://github.com/Emzime/Chia_Log_Monitor.git`<br><br>
    
Se déplacer dans le répertoire du projet : <br>
    `cd Chia_Log_Monitor`<br><br>

Créer et activer un environnement virtuel : <br>
    `python -m venv venv .\venv\Scripts\activate`<br><br>

Construction : <br>
    `python build.bat`<br><br><br>
