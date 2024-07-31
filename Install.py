import subprocess
import sys

# Définir les bibliothèques nécessaires
required_libraries = [
    'matplotlib',
    'mplcursors'
]

# Sous-modules pour vérification complète (inclus pour la clarté, mais pas installés via pip)
submodules = [
    'os',
    'platform',
    're',
    'sys',
    'threading',
    'tkinter',
    'collections',
    'datetime',
    'tkinter.messagebox',
    'tkinter.ttk',
    'tkinter.filedialog',
    'matplotlib.dates',
    'matplotlib.pyplot',
    'matplotlib.ticker',
    'matplotlib.backends.backend_tkagg'
]


# Vérifier l'installation de chaque bibliothèque
def check_installation(library):
    try:
        __import__(library)
        print(f"{library} est déjà installé.")
        return True
    except ImportError:
        print(f"{library} n'est pas installé.")
        return False


# Vérifier l'installation des sous-modules de la bibliothèque standard
def check_submodules():
    for submodule in submodules:
        try:
            __import__(submodule)
            print(f"{submodule} est déjà présent.")
        except ImportError:
            print(f"Erreur: {submodule} n'est pas présent, cela pourrait indiquer un problème avec votre installation de Python.")


# Installer une bibliothèque avec pip
def install_library(library):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", library])
        print(f"{library} a été installé avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'installation de {library}: {e}")
        sys.exit(1)


# Vérifier et installer les bibliothèques nécessaires
def check_and_install_libraries():
    for lib in required_libraries:
        if not check_installation(lib):
            print(f"Installation de {lib}...")
            install_library(lib)
    check_submodules()


# Fonction principale pour démarrer le script principal
def run_main_script():
    try:
        from Chia_Log_Monitor import main
        main()
    except ImportError:
        print("Le script principal Chia_Log_Monitor.py est introuvable.")
        sys.exit(1)


if __name__ == "__main__":
    check_and_install_libraries()
