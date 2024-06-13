import subprocess
import sys

# Définir les bibliothèques nécessaires
required_libraries = ['matplotlib']


# Vérifier l'installation de chaque bibliothèque
def check_installation(library):
    try:
        __import__(library)
        print(f"{library} est déjà installé.")
        return True
    except ImportError:
        print(f"{library} n'est pas installé.")
        return False


# Installer une bibliothèque avec pip
def install_library(library):
    subprocess.check_call([sys.executable, "-m", "pip", "install", library])


# Vérifier et installer les bibliothèques nécessaires
def check_and_install_libraries():
    for lib in required_libraries:
        if not check_installation(lib):
            print(f"Installation de {lib}...")
            try:
                install_library(lib)
            except subprocess.CalledProcessError as e:
                print(f"Erreur lors de l'installation de {lib}: {e}")
                sys.exit(1)


# Fonction principale pour démarrer le script principal
def run_main_script():
    try:
        from chia_log_monitor import main
        main()
    except ImportError:
        print("Le script principal chia_log_monitor.py est introuvable.")
        sys.exit(1)


if __name__ == "__main__":
    check_and_install_libraries()
    run_main_script()
