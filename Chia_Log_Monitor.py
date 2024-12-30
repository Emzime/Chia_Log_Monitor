import os
import platform
import re
import sys
import threading
import tkinter as tk
from collections import defaultdict
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import mplcursors
from matplotlib import ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Chemin du log par défaut
system = platform.system()
if system == "Linux":
    default_log_file = os.path.expanduser("~/.chia/mainnet/log/debug.log")
elif system == "Windows":
    default_log_file = os.path.expandvars(r"%systemdrive%\%homepath%\.chia\mainnet\log\debug.log")
elif system == "Darwin":  # MacOS
    default_log_file = os.path.expanduser("~/Library/Application Support/Chia/mainnet/log/debug.log")
else:
    # Si le système n'est pas reconnu, vous devez définir manuellement le chemin ici
    default_log_file = ""

personal_log = r'\\VM-CHIA\.chia\mainnet\log\debug.log'
# personal_log = r'\\FARMER\log\debug.log'

# Regex de recherche des logs
log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}) \S+ harvester chia\.harvester\.harvester: INFO\s+(\d+) plots were eligible for farming \w+\.\.\. Found (\d+) proofs\. Time: ([\d.]+) s\. Total (\d+) plots')
pool_info_pattern = re.compile(r"GET /pool_info response:\s+({.*})")
farmer_info_pattern = re.compile(r"GET /farmer response:\s+({.*})")
giga_horse_fee_pattern = re.compile(r"fee_rate = (?P<fee_rate>\d+\.\d+) %")
points_pattern = re.compile(r"Points: (\d+)")

log_data = defaultdict(list)
pool_info = {}
farmer_info = {}

# Définition des couleurs
font_family = "Arial"
color_yellow = "#FFFF80"
color_red = "#FF4500"
color_blue = "#5385F6"
color_green = "#00FF00"
color_black = "#000000"
color_white = "#FFFFFF"
color_dark_gray = "#333333"
color_medium_grey = "#666666"
color_light_gray = "#999999"
color_very_light_gray = "#E6E6E6"


def on_enter(event):
    # Change the style to the hover style
    event.widget.configure(style="Hover.Vertical.TScrollbar")


def on_leave(event):
    # Change the style back to the normal style
    event.widget.configure(style="Normal.Vertical.TScrollbar")


def parse_log_line(line):
    match = log_pattern.match(line)
    if match:
        timestamp_str = match.group(1)
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
        eligible_plots = int(match.group(2))
        proofs_found = int(match.group(3))
        time_taken = float(match.group(4))
        total_plots = int(match.group(5))
        return timestamp, eligible_plots, proofs_found, time_taken, total_plots
    return None


def parse_pool_info(line):
    match = pool_info_pattern.search(line)
    if match:
        info = eval(match.group(1))
        pool_info['name'] = info.get('name')
        pool_info['discord'] = info.get('description').split(' ')[-1].strip('()')
        pool_info['fee'] = info.get('fee')
        return True
    return False


def parse_farmer_info(line):
    match = farmer_info_pattern.search(line)
    if match:
        info = eval(match.group(1))  # Using eval for simplicity, but json.loads is safer for actual use
        farmer_info['current_difficulty'] = info.get('current_difficulty')
        farmer_info['current_points'] = info.get('current_points')
        return True
    return False


def parse_giga_horse_info(log_lines):
    for line in log_lines:
        if "Found proof" in line:
            match = giga_horse_fee_pattern.search(line)
            if match:
                info = match.groupdict()
                return float(info.get('fee_rate'))
    return False


def parse_points(line):
    match = points_pattern.search(line)
    if match:
        points = int(match.group(1))
        log_data['points'].append(points)
        return True
    return False


def print_summary(text_widget):
    total_entries = len(log_data['timestamp'])
    if total_entries == 0:
        return "No log data found."

    special_color = color_green

    detailed_summary = "Résumé détaillé du journal:\n\n"
    for i in range(total_entries):
        detailed_summary += (f"{log_data['timestamp'][i]} - Parcelles admissibles: {log_data['eligible_plots'][i]}, "
                             f"Preuves trouvées: {log_data['proofs_found'][i]}, "
                             f"Temps pris: {log_data['time_taken'][i]:.2f} s, "
                             f"Total des parcelles: {log_data['total_plots'][i]}\n")

    # Insertion du texte avec balises
    if text_widget:
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, detailed_summary)

        # Ajouter une balise pour le titre "Résumé détaillé du journal"
        title_index = text_widget.search("Résumé détaillé du journal", "1.0", tk.END)
        if title_index:
            end_title_index = text_widget.index(f"{title_index} + {len('Résumé détaillé du journal')} chars")
            text_widget.tag_add("title", title_index, end_title_index)
            text_widget.tag_configure("title", foreground=special_color)


def print_summary_stats(text_widget):
    if not log_data['timestamp']:
        text_widget.delete('1.0', tk.END)
        text_widget.insert(tk.END, "Aucune donnée de journal trouvée.")
        return

    # Mise à jour du pourcentage de preuves
    calculate_proof_times(log_data['time_taken'])
    calculate_proof_info()

    total_entries = len(log_data['timestamp'])
    min_proof_time, max_proof_time, avg_proof_time = calculate_proof_times(log_data['time_taken'])
    total_proofs_found = sum(log_data['proofs_found'])
    total_plots = log_data['total_plots'][-1] if log_data['total_plots'] else 0

    # Mise à jour du nombre de preuves
    proof_info_le_8, proof_info_gt_8 = calculate_proof_info()

    # Récupère depuis quand le log a été créé
    elapsed_time_formatted = calculate_elapsed_time()

    # Récupère les informations du pool
    pool_name, pool_discord, pool_fee = extract_pool_info()

    # Récupère les informations du farmer
    current_difficulty, current_points = extract_farmer_info()

    # Récupère les informations de GigaHorse
    fee_rate = parse_giga_horse_info(log_data['giga_horse_info'])
    if fee_rate is not False and fee_rate is not None:
        fee_rate = f"{fee_rate}%"
    else:
        fee_rate = "Données en attente"

    # Affiche l'heure de la dernière mise à jour
    last_update_time = datetime.now().strftime('%H:%M:%S')

    # Affiche l'heure de la dernière preuve <= 8 sec
    last_proof_le_8_time = "Aucune preuve inférieure à 8 sec trouvée"
    if total_proofs_found > 0:
        last_proof_le_8_indices = [
            i for i, (proof, time_taken) in enumerate(zip(log_data['proofs_found'], log_data['time_taken']))
            if proof > 0 and time_taken <= 8
        ]
        if last_proof_le_8_indices:
            last_proof_le_8_day = log_data['timestamp'][last_proof_le_8_indices[-1]].strftime('%d/%m/%Y')
            last_proof_le_8_time = log_data['timestamp'][last_proof_le_8_indices[-1]].strftime('%H heures %M minutes %S secondes')
            last_proof_le_8_time = f"Dernière preuve inférieure à 8 sec trouvée le {last_proof_le_8_day} à {last_proof_le_8_time}"

    # Affiche l'heure de la dernière preuve > 8 sec
    last_proof_gt_8_time = "Aucune preuve supérieure à 8 sec trouvée"
    if total_proofs_found > 0:
        last_proof_gt_8_indices = [
            i for i, (proof, time_taken) in enumerate(zip(log_data['proofs_found'], log_data['time_taken']))
            if proof > 0 and time_taken > 8
        ]
        if last_proof_gt_8_indices:
            last_proof_gt_8_day = log_data['timestamp'][last_proof_gt_8_indices[-1]].strftime('%d/%m/%Y')
            last_proof_gt_8_time = log_data['timestamp'][last_proof_gt_8_indices[-1]].strftime('%H heures %M minutes %S secondes')
            last_proof_gt_8_time = f"Dernière preuve supérieure à 8 sec trouvée le {last_proof_gt_8_day} à {last_proof_gt_8_time}"

    # Crée l'affichage des statistiques
    summary_stats = (
        ":: Infos sur la pool ::\n"
        f" Nom: {pool_name}\n"
        f" Discord: {pool_discord}\n"
        f" Fee: {pool_fee}%\n"

        "\n:: Infos sur la ferme ::\n"
        f" Total de parcelles: {total_plots}\n"
        f" Difficulté de la ferme: {current_difficulty}\n"
        f" Points de la ferme: {current_points}\n"

        "\n:: Infos sur les preuves ::\n"
        f" Total des entrées: {total_entries}\n"
        f" Total des preuves trouvées: {total_proofs_found}\n"
        f" {proof_info_le_8}\n"
        f" {proof_info_gt_8}\n\n"

        f" Temps minimal des preuves: {min_proof_time:.2f} secondes\n"
        f" Temps moyen des preuves: {avg_proof_time:.2f} secondes\n"
        f" Temps maximal des preuves: {max_proof_time:.2f} secondes\n\n"

        f" {last_proof_le_8_time}\n"
        f" {last_proof_gt_8_time}\n\n"

        "\n:: Autres données ::\n"
        f" GigaHorse Fee: {fee_rate}\n"
        f" Temps écoulé depuis le début du log: {elapsed_time_formatted}\n\n"

        f"Dernière mise à jour: {last_update_time}\n"
    )

    # Insertion du texte avec balises
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, summary_stats)

    # Configurer les balises pour la section
    color_special = color_yellow
    color_update_time = color_green

    # Appliquer les balises pour les sections spéciales et l'heure de mise à jour
    lines = summary_stats.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("::") and line.endswith("::"):
            start_index = f"{i + 1}.0"
            end_index = f"{i + 1}.0 + {len(line)} chars"
            text_widget.tag_add("special", start_index, end_index)
            text_widget.tag_configure("special", foreground=color_special)
        if line.startswith("Dernière mise à jour:"):
            start_index = f"{i + 1}.0"
            end_index = f"{i + 1}.0 + {len(line)} chars"
            text_widget.tag_add("update_time", start_index, end_index)
            text_widget.tag_configure("update_time", foreground=color_update_time)


def calculate_proof_times(time_taken_list):
    if not time_taken_list:
        return None, None, None

    min_time = min(time_taken_list)
    max_time = max(time_taken_list)
    avg_time = sum(time_taken_list) / len(time_taken_list)
    return min_time, max_time, avg_time


def calculate_proof_info():
    time_taken_le_8 = [time for time in log_data['time_taken'] if time <= 8]
    time_taken_gt_8 = [time for time in log_data['time_taken'] if time > 8]

    total_count_le_8 = len(time_taken_le_8)
    total_count_gt_8 = len(time_taken_gt_8)

    total_proofs = total_count_le_8 + total_count_gt_8
    if total_proofs > 0:
        proof_percentage_gt_8 = (total_count_gt_8 / total_proofs) * 100
        proof_percentage_le_8 = 100 - proof_percentage_gt_8
    else:
        proof_percentage_gt_8 = 0.0
        proof_percentage_le_8 = 0.0

    proof_info_le_8 = f"Total de preuves inférieures à 8 secondes: {total_count_le_8} ({proof_percentage_le_8:.2f}%)"
    proof_info_gt_8 = f"Total de preuves supérieures à 8 secondes: {total_count_gt_8} ({proof_percentage_gt_8:.2f}%)\n"

    return proof_info_le_8, proof_info_gt_8


def calculate_elapsed_time():
    first_timestamp = log_data['timestamp'][0]
    last_timestamp = log_data['timestamp'][-1]
    elapsed_time = last_timestamp - first_timestamp
    return format_elapsed_time(elapsed_time)


def extract_pool_info():
    pool_name = pool_info.get('name', 'Données en attente')
    pool_discord = pool_info.get('discord', 'Données en attente')
    pool_fee = pool_info.get('fee', 'Données en attente')
    return pool_name, pool_discord, pool_fee


def extract_farmer_info():
    current_difficulty = farmer_info.get('current_difficulty', 'Données en attente')
    current_points = farmer_info.get('current_points', 'Données en attente')
    return current_difficulty, current_points


# Fonction pour formater le temps écoulé en jours, heures, minutes et secondes
def format_elapsed_time(elapsed_time):
    days = elapsed_time.days
    hours, remainder = divmod(elapsed_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    formatted_time = ""
    if days > 0:
        formatted_time += f"{days} jour{'s' if days > 1 else ''} "
    if hours > 0:
        formatted_time += f"{hours} heure{'s' if hours > 1 else ''} "
    if minutes > 0:
        formatted_time += f"{minutes} minute{'s' if minutes > 1 else ''} "

    # Gérer l'affichage des secondes avec précision
    if seconds.is_integer():
        formatted_time += f"{int(seconds)} seconde{'s' if seconds != 1 else ''}"
    else:
        formatted_time += f"{seconds:.2f} secondes"

    return formatted_time


def resource_path(relative_path):
    """Obtenir le chemin absolu vers la ressource, fonctionne pour dev et pour PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base_path, relative_path)


class LogMonitorApp:
    def __init__(self, root):
        # Initialisation de l'application et des variables
        self.root = root
        self.root.title("Chia Log Monitor")
        # Set dark background for the root window
        self.root.configure(bg=color_dark_gray)

        # Construire le chemin complet de l'icône
        self.root.iconbitmap(resource_path("images/icon.ico"))

        # Centrer sur l'écran
        self.center_window(1750, 768)

        # Indicateur de chargement du log
        self.log_loaded = False
        # Verrou pour synchroniser l'accès à log_loaded
        self.log_loaded_lock = threading.Lock()
        self.last_file_size = 0
        self.monitor_file_path = ""

        # Initialize custom style for progress bar
        self.custom_style = ttk.Style()
        self.custom_style.theme_use('default')

        # Normal style Progress_Bar
        self.custom_style.configure(
            "Normal.Vertical.TProgressbar",
            troughcolor=color_dark_gray,  # La couleur du canal où se déplace la barre de défilement
            background=color_green,  # La couleur de la barre de défilement
            arrowcolor=color_black,  # La couleur des flèches de la scrollbar
        )

        # Normal style Scrollbar
        self.custom_style.configure(
            "Normal.Vertical.TScrollbar",
            troughcolor=color_dark_gray,  # La couleur du canal où se déplace la barre de défilement
            background=color_medium_grey,  # La couleur de la barre de défilement
            arrowcolor=color_black,  # La couleur des flèches de la scrollbar
        )

        # Hover style Scrollbar
        self.custom_style.configure(
            "Hover.Vertical.TScrollbar",
            troughcolor=color_dark_gray,  # La couleur du canal où se déplace la barre de défilement
            background=color_medium_grey,  # La couleur de la barre de défilement
            arrowcolor=color_green,  # La couleur des flèches de la scrollbar
        )

        self.progress_bar = ttk.Progressbar(self.root, style="Normal.Vertical.TProgressbar", orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=0, column=0, padx=5, pady=0, ipady=8, sticky=tk.NSEW)

        self.percentage_label = tk.Label(self.progress_bar, text="")
        self.loading_label = tk.Label(self.progress_bar, text="")

        self.frame = tk.Frame(self.root, bg=color_dark_gray)
        self.frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)

        self.load_button = tk.Button(self.frame, text="Charger le fichier de logs", command=lambda: self.load_log_file(), bg='#999999', fg='#000000')
        self.load_button.grid(row=0, column=0, columnspan=2, padx=10, pady=(20, 5), sticky=tk.N)

        self.top_frame = tk.Frame(self.frame, bg=color_dark_gray)
        self.top_frame.grid(row=1, column=0, sticky=tk.NSEW)

        self.summary_frame = tk.Frame(self.top_frame, bd=2, relief=tk.SUNKEN, bg=color_dark_gray)
        self.summary_frame.grid(row=0, column=0, padx=5, pady=(10, 5), sticky=tk.NSEW)

        self.summary_text = tk.Text(self.summary_frame, wrap=tk.WORD, height=30, bg=color_dark_gray, fg=color_white, font=(font_family, 11))
        self.summary_text.grid(row=0, column=0, sticky=tk.NSEW)

        self.summary_scrollbar = ttk.Scrollbar(self.summary_frame, orient=tk.VERTICAL, style="Normal.Vertical.TScrollbar", command=self.summary_text.yview)
        self.summary_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.summary_text.configure(yscrollcommand=self.summary_scrollbar.set, padx=10, pady=5)

        # Bind enter and leave events to the scrollbar
        self.summary_scrollbar.bind("<Enter>", on_enter)
        self.summary_scrollbar.bind("<Leave>", on_leave)

        self.stats_frame = tk.Frame(self.top_frame, bd=2, relief=tk.SUNKEN, bg=color_dark_gray)
        self.stats_frame.grid(row=0, column=1, padx=5, pady=(10, 5), sticky=tk.NSEW)

        self.stats_text = tk.Text(self.stats_frame, wrap=tk.WORD, height=30, bg=color_dark_gray, fg=color_white, font=(font_family, 11))
        self.stats_text.grid(row=0, column=0, sticky=tk.NSEW)

        self.stats_scrollbar = ttk.Scrollbar(self.stats_frame, orient=tk.VERTICAL, style="Normal.Vertical.TScrollbar", command=self.stats_text.yview)
        self.stats_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.stats_text.configure(yscrollcommand=self.stats_scrollbar.set, padx=10, pady=5)

        # Bind enter and leave events to the scrollbar
        self.stats_scrollbar.bind("<Enter>", on_enter)
        self.stats_scrollbar.bind("<Leave>", on_leave)

        self.bottom_frame = tk.Frame(root, bg=color_dark_gray)
        self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)

        self.plot_frame1 = tk.Frame(self.bottom_frame, bd=2, relief=tk.SUNKEN, bg=color_dark_gray)
        self.plot_frame1.grid(row=0, column=0, padx=5, pady=(5, 10), sticky=tk.NSEW)

        self.plot_frame2 = tk.Frame(self.bottom_frame, bd=2, relief=tk.SUNKEN, bg=color_dark_gray)
        self.plot_frame2.grid(row=0, column=1, padx=5, pady=(5, 10), sticky=tk.NSEW)

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.top_frame.grid_rowconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=1)

        self.summary_frame.grid_rowconfigure(0, weight=1)
        self.summary_frame.grid_columnconfigure(0, weight=1)

        self.stats_frame.grid_rowconfigure(0, weight=1)
        self.stats_frame.grid_columnconfigure(0, weight=1)

        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)

        self.plot_frame1.grid_rowconfigure(0, weight=1)
        self.plot_frame1.grid_columnconfigure(0, weight=1)
        self.fig1, self.ax1 = plt.subplots(figsize=(8, 6))

        self.plot_frame2.grid_rowconfigure(0, weight=1)
        self.plot_frame2.grid_columnconfigure(0, weight=1)
        self.fig2, self.ax2 = plt.subplots(figsize=(8, 6))

        # Create canvas instances and grid them
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.plot_frame1)
        self.canvas1.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.plot_frame2)
        self.canvas2.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)

        # Initialize cursor attributes
        self.cursor1 = None
        self.cursor2 = None

        # Sets the style of the chart
        self.fig1.patch.set_facecolor(color_dark_gray)
        self.ax1.set_facecolor(color_dark_gray)
        self.ax1.tick_params(axis='x', colors=color_dark_gray)
        self.ax1.tick_params(axis='y', colors=color_dark_gray)
        self.ax1.spines['bottom'].set_color(color_dark_gray)
        self.ax1.spines['top'].set_color(color_dark_gray)
        self.ax1.spines['left'].set_color(color_dark_gray)
        self.ax1.spines['right'].set_color(color_dark_gray)
        self.ax1.title.set_color(color_white)
        self.ax1.xaxis.label.set_color(color_dark_gray)
        self.ax1.yaxis.label.set_color(color_dark_gray)

        # Sets the style of the chart
        self.fig2.patch.set_facecolor(color_dark_gray)
        self.ax2.set_facecolor(color_dark_gray)
        self.ax2.tick_params(axis='x', colors=color_dark_gray)
        self.ax2.tick_params(axis='y', colors=color_dark_gray)
        self.ax2.spines['bottom'].set_color(color_dark_gray)
        self.ax2.spines['top'].set_color(color_dark_gray)
        self.ax2.spines['left'].set_color(color_dark_gray)
        self.ax2.spines['right'].set_color(color_dark_gray)
        self.ax2.title.set_color(color_white)
        self.ax2.xaxis.label.set_color(color_dark_gray)
        self.ax2.yaxis.label.set_color(color_dark_gray)

        # Load default log file and start periodic update
        self.load_default_log_file()

        if not self.log_loaded:
            self.update_ui()

        if self.log_loaded:
            self.update_periodically()

    def read_log_file(self, file_path):
        try:
            # Display the progress bar at the beginning of file reading
            self.progress_bar.grid(row=1, column=0, columnspan=2, padx=(215, 5), ipady=8, sticky=tk.NSEW)

            # Place the loading message in the middle of the progress bar
            self.loading_label = tk.Label(self.root, text="Chargement en cours: ", background=color_dark_gray, foreground=color_green, font=(font_family, 11, 'bold'))
            self.loading_label.grid(row=1, column=0, columnspan=2, padx=5, ipadx=5, ipady=7, sticky=tk.NW)

            # Place the percentage label
            self.percentage_label = tk.Label(self.root, text="", background=color_dark_gray, foreground=color_green, font=(font_family, 11))
            self.percentage_label.grid(row=1, column=0, columnspan=2, padx=(173, 0), ipadx=5, ipady=7, sticky=tk.NW)

            with open(file_path, 'r') as file:
                file_lines = file.readlines()
                self.progress_bar['maximum'] = len(file_lines)

                for line in file_lines:
                    # Parsing log lines
                    parsed_line = parse_log_line(line)
                    if parsed_line:
                        timestamp, eligible_plots, proofs_found, time_taken, total_plots = parsed_line
                        log_data['timestamp'].append(timestamp)
                        log_data['eligible_plots'].append(eligible_plots)
                        log_data['proofs_found'].append(proofs_found)
                        log_data['time_taken'].append(time_taken)
                        log_data['total_plots'].append(total_plots)
                    else:
                        # Parsing other info
                        if not parse_pool_info(line) and not parse_farmer_info(line) and not parse_points(line):
                            parse_giga_horse_info(line)

                    self.progress_bar.step(1)
                    # Mettre à jour la barre de progression
                    self.progress_bar.update_idletasks()
                    # Mise à jour du pourcentage
                    self.percentage_label.config(text=f"{int((self.progress_bar['value'] / self.progress_bar['maximum']) * 100)}%")

            # Marquer le chargement comme terminé en toute sécurité avec le verrou
            with self.log_loaded_lock:
                self.log_loaded = True

            # Appeler update_ui après la fin du chargement
            self.root.after(0, self.update_ui)

        except FileNotFoundError:
            messagebox.showerror("Erreur de fichier", f"Le fichier de log '{file_path}' est introuvable.")
        except Exception as e:
            messagebox.showerror("Erreur de lecture", f"Une erreur est survenue lors de la lecture du fichier de log : {str(e)}")
        finally:
            # Cacher le message de chargement une fois la lecture terminée
            self.loading_label.grid_remove()
            # Assurez-vous que la barre de progression est cachée à la fin
            self.progress_bar.grid_remove()
            self.percentage_label.config(text="")
            # Signalisation de la fin du chargement
            self.log_loaded = True

    def load_log_file(self):
        # Réinitialiser le statut de chargement
        self.log_loaded = False

        file_path = filedialog.askopenfilename(filetypes=[("Log Files", "*.log")])
        if file_path:
            self.root.after(50, self.start_read_log_file, file_path)

    def load_default_log_file(self):
        # Réinitialiser le statut de chargement
        self.log_loaded = False

        if os.path.exists(default_log_file):
            self.root.after(50, self.start_read_log_file, default_log_file)
        elif os.path.exists(personal_log):
            self.root.after(50, self.start_read_log_file, personal_log)
        else:
            messagebox.showerror("Erreur de fichier", "Les fichiers de log sont introuvables.")

    def read_new_lines(self, file_path):
        current_size = os.path.getsize(file_path)
        if current_size > self.last_file_size:
            with open(file_path, 'r') as file:
                # Commencez à lire à partir de la dernière position lue
                file.seek(self.last_file_size)
                new_lines = file.readlines()
                # Mettre à jour la dernière taille du fichier
                self.last_file_size = current_size

                for line in new_lines:
                    parsed_line = parse_log_line(line)
                    if parsed_line:
                        timestamp, eligible_plots, proofs_found, time_taken, total_plots = parsed_line
                        log_data['timestamp'].append(timestamp)
                        log_data['eligible_plots'].append(eligible_plots)
                        log_data['proofs_found'].append(proofs_found)
                        log_data['time_taken'].append(time_taken)
                        log_data['total_plots'].append(total_plots)
                    else:
                        if not parse_pool_info(line) and not parse_farmer_info(line) and not parse_points(line):
                            parse_giga_horse_info(line)

                self.update_ui()

                if hasattr(self, 'log_loaded') and self.log_loaded:
                    self.plot_data()
                    self.set_chart_style()

    def start_monitoring(self, file_path):
        self.last_file_size = os.path.getsize(file_path)
        self.monitor_file_path = file_path
        self.root.after(1000, self.update_log_file)

    def update_log_file(self):
        self.read_new_lines(self.monitor_file_path)
        self.root.after(1000, self.update_log_file)

    def start_read_log_file(self, file_path):
        thread = threading.Thread(target=self.read_log_file, args=(file_path,))
        thread.daemon = True
        thread.start()
        self.start_monitoring(file_path)

    def update_periodically(self):
        # Update UI periodically
        self.update_ui()
        self.root.after(1000, self.update_periodically)

        if hasattr(self, 'log_loaded') and self.log_loaded:
            self.plot_data()
            self.set_chart_style()

    def update_ui(self):
        # Sauvegarder la position actuelle de défilement
        current_summary_yview = self.summary_text.yview()
        current_stats_yview = self.stats_text.yview()

        # Mettre à jour le texte de résumé et les statistiques
        print_summary(self.summary_text)
        print_summary_stats(self.stats_text)

        # Restaurez la position de défilement
        self.summary_text.yview_moveto(current_summary_yview[0])
        self.stats_text.yview_moveto(current_stats_yview[0])

        self.summary_text.see(tk.END)
        self.stats_text.see(tk.END)

    def set_chart_style(self):
        # Sets the style of the chart
        self.fig1.patch.set_facecolor(color_dark_gray)
        self.ax1.set_facecolor(color_dark_gray)
        self.ax1.tick_params(axis='x', colors=color_white)
        self.ax1.tick_params(axis='y', colors=color_white)
        self.ax1.spines['bottom'].set_color(color_white)
        self.ax1.spines['top'].set_color(color_dark_gray)
        self.ax1.spines['left'].set_color(color_white)
        self.ax1.spines['right'].set_color(color_dark_gray)
        self.ax1.title.set_color(color_white)
        self.ax1.xaxis.label.set_color(color_white)
        self.ax1.yaxis.label.set_color(color_white)

        # Sets the style of the chart
        self.fig2.patch.set_facecolor(color_dark_gray)
        self.ax2.set_facecolor(color_dark_gray)
        self.ax2.tick_params(axis='x', colors=color_white)
        self.ax2.tick_params(axis='y', colors=color_white)
        self.ax2.spines['bottom'].set_color(color_white)
        self.ax2.spines['top'].set_color(color_dark_gray)
        self.ax2.spines['left'].set_color(color_white)
        self.ax2.spines['right'].set_color(color_dark_gray)
        self.ax2.title.set_color(color_white)
        self.ax2.xaxis.label.set_color(color_white)
        self.ax2.yaxis.label.set_color(color_white)

    def plot_data(self):
        if hasattr(self, 'log_loaded') and self.log_loaded:
            if not log_data['timestamp']:
                return

            # Calculer l'heure actuelle moins une heure
            now = datetime.now()
            start_time = now - timedelta(minutes=60)

            # Filtrer les données pour ne garder que celles dans l'intervalle de la dernière heure
            filtered_data = {
                '<= 8 sec': [],
                '> 8 sec': []
            }

            for timestamp, time_taken, proofs_found, eligible_plots in zip(log_data['timestamp'], log_data['time_taken'], log_data['proofs_found'], log_data['eligible_plots']):
                if timestamp >= start_time:
                    if time_taken <= 8:
                        filtered_data['<= 8 sec'].append((timestamp, time_taken, proofs_found, eligible_plots))
                    else:
                        filtered_data['> 8 sec'].append((timestamp, time_taken, proofs_found, eligible_plots))

            # Préparer les données pour le graphique 1 (<= 8 secondes)
            timestamps_le_8 = [data[0] for data in filtered_data['<= 8 sec']]
            time_taken_le_8 = [data[1] for data in filtered_data['<= 8 sec']]
            proofs_found_le_8 = [data[2] for data in filtered_data['<= 8 sec']]
            eligible_plots_le_8 = [data[3] for data in filtered_data['<= 8 sec']]

            # Préparer les données pour le graphique 2 (> 8 secondes)
            timestamps_gt_8 = [data[0] for data in filtered_data['> 8 sec']]
            time_taken_gt_8 = [data[1] for data in filtered_data['> 8 sec']]
            proofs_found_gt_8 = [data[2] for data in filtered_data['> 8 sec']]
            eligible_plots_gt_8 = [data[3] for data in filtered_data['> 8 sec']]

            # Filtrer les données avec preuves trouvées pour all_proof_graphs
            self.all_proof_graphs(timestamps_le_8, time_taken_le_8, proofs_found_le_8, eligible_plots_le_8, timestamps_gt_8, time_taken_gt_8, proofs_found_gt_8, eligible_plots_gt_8)

            # Filtrer les données avec preuves trouvées > 0 pour found_proof_graph
            timestamps_le_8_filtered, proofs_found_le_8_filtered, time_taken_le_8_filtered, eligible_plots_le_8_filtered = self.filter_data(timestamps_le_8, proofs_found_le_8, time_taken_le_8, eligible_plots_le_8)
            timestamps_gt_8_filtered, proofs_found_gt_8_filtered, time_taken_gt_8_filtered, eligible_plots_gt_8_filtered = self.filter_data(timestamps_gt_8, proofs_found_gt_8, time_taken_gt_8, eligible_plots_gt_8)
            self.found_proof_graphs(timestamps_le_8_filtered, time_taken_le_8_filtered, eligible_plots_le_8_filtered, proofs_found_le_8_filtered, timestamps_gt_8_filtered, time_taken_gt_8_filtered, eligible_plots_gt_8_filtered,
                                    proofs_found_gt_8_filtered)

    @staticmethod
    def filter_data(timestamps, proofs_found, time_taken, eligible_plots):
        timestamps_filtered = [ts for ts, proof in zip(timestamps, proofs_found) if proof > 0]
        proofs_found_filtered = [proof for proof in proofs_found if proof > 0]
        time_taken_filtered = [time for time, proof in zip(time_taken, proofs_found) if proof > 0]
        eligible_plots_filtered = [plots for plots, proof in zip(eligible_plots, proofs_found) if proof > 0]

        return timestamps_filtered, proofs_found_filtered, time_taken_filtered, eligible_plots_filtered

    def all_proof_graphs(self, timestamps_le_8, time_taken_le_8, proofs_found_le_8, eligible_plots_le_8, timestamps_gt_8, time_taken_gt_8, proofs_found_gt_8, eligible_plots_gt_8):
        # Efface les tracés précédents
        self.ax1.cla()

        # Déterminer le début et la fin de la période à afficher
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=60)

        # Filtrage des données
        timestamps_le_8_filtered = [ts for ts in timestamps_le_8 if ts >= start_time]
        time_taken_le_8_filtered = [time_taken_le_8[i] for i, ts in enumerate(timestamps_le_8) if ts >= start_time]
        proofs_found_le_8_filtered = [proofs_found_le_8[i] for i, ts in enumerate(timestamps_le_8) if ts >= start_time]

        timestamps_gt_8_filtered = [ts for ts in timestamps_gt_8 if ts >= start_time]
        time_taken_gt_8_filtered = [time_taken_gt_8[i] for i, ts in enumerate(timestamps_gt_8) if ts >= start_time]
        proofs_found_gt_8_filtered = [proofs_found_gt_8[i] for i, ts in enumerate(timestamps_gt_8) if ts >= start_time]

        # Ajouter des marqueurs pour <= 8 secondes sans relier avec des lignes
        scatter_le_8 = self.ax1.scatter(timestamps_le_8_filtered, time_taken_le_8_filtered, color=color_green, marker='o', s=25)

        # Ajouter des marqueurs pour > 8 secondes sans relier avec des lignes
        scatter_gt_8 = self.ax1.scatter(timestamps_gt_8_filtered, time_taken_gt_8_filtered, color=color_red, marker='o', s=25, label='> 8 secondes')

        # Ajouter des points pour proofs_found_le_8 > 0 sans relier avec des lignes
        for x, y, proof in zip(timestamps_le_8_filtered, time_taken_le_8_filtered, proofs_found_le_8_filtered):
            if proof > 0:
                self.ax1.scatter(x, y, color=color_blue, marker='o', s=25)

        # Ajouter des points pour proofs_found_gt_8 > 0 sans relier avec des lignes
        for x, y, proof in zip(timestamps_gt_8_filtered, time_taken_gt_8_filtered, proofs_found_gt_8_filtered):
            if proof > 0:
                self.ax1.scatter(x, y, color=color_blue, marker='o', s=25)

        # Ajouter le quadrillage à l'arrière-plan
        self.ax1.axhline(y=8, color=color_white, linestyle='--', linewidth=0.5)
        self.ax1.set_title('Temps de toutes les preuves sur la dernière heure', color=color_white)

        # Définition du formateur personnalisé pour l'axe x
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Hh%M'))

        # Définir la limite temporelle de la dernière heure
        self.ax1.set_xlim(start_time, end_time)

        # Calculer la limite maximale de l'axe Y
        max_time_taken = max(max(time_taken_le_8_filtered, default=0), max(time_taken_gt_8_filtered, default=0))
        y_upper_limit = max_time_taken + 2 if max_time_taken > 10 else 10
        self.ax1.set_ylim(0, y_upper_limit)

        # Utilisation de MaxNLocator pour limiter le nombre de ticks sur l'axe x
        self.ax1.xaxis.set_major_locator(ticker.MaxNLocator(20))
        self.fig1.autofmt_xdate()

        # Gérer les tooltips avec mplcursors
        if self.cursor1:
            self.cursor1.visible = False

        # Créez un curseur pour les objets scatter
        self.cursor1 = mplcursors.cursor([scatter_le_8, scatter_gt_8], hover=True)

        @self.cursor1.connect("add")
        def on_add_cursor1(sel):
            tooltip_color = color_white
            face_color = color_black
            artist = sel.artist

            # Vérifier si l'artiste est un scatter
            if artist == scatter_le_8:
                index = sel.index
                if 0 <= index < len(timestamps_le_8_filtered):
                    ts = timestamps_le_8_filtered[index]
                    parcelles = eligible_plots_le_8[index]
                    temps = time_taken_le_8_filtered[index]
                    sel.annotation.set(text=f"{ts.strftime('%d-%m-%Y %H:%M:%S')}\n"
                                            f"Parcelles éligibles: {parcelles}\n"
                                            f"Preuves trouvées: {proofs_found_le_8_filtered[index]}\n"
                                            f"Temps: {temps:.2f} s",
                                       color=tooltip_color,
                                       bbox=dict(facecolor=face_color, edgecolor='none'),
                                       ha='left')
            elif artist == scatter_gt_8:
                index = sel.index
                if 0 <= index < len(timestamps_gt_8_filtered):
                    ts = timestamps_gt_8_filtered[index]
                    parcelles = eligible_plots_gt_8[index]
                    temps = time_taken_gt_8_filtered[index]
                    sel.annotation.set(text=f"{ts.strftime('%d-%m-%Y %H:%M:%S')}\n"
                                            f"Parcelles éligibles: {parcelles}\n"
                                            f"Preuves trouvées: {proofs_found_gt_8_filtered[index]}\n"
                                            f"Temps: {temps:.2f} s",
                                       color=tooltip_color,
                                       bbox=dict(facecolor=face_color, edgecolor='none'),
                                       ha='left')
            else:
                sel.annotation.set(text="",
                                   color=tooltip_color,
                                   bbox=dict(facecolor=face_color, edgecolor='none'),
                                   ha='left')

        # Redessine le canevas
        self.canvas1.draw()

    def found_proof_graphs(self, timestamps_le_8, time_taken_le_8, eligible_plots_le_8, proofs_found_le_8, timestamps_gt_8, time_taken_gt_8, eligible_plots_gt_8, proofs_found_gt_8):
        # Clear previous plots
        self.ax2.cla()

        # Déterminer le début et la fin de la période à afficher
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=60)

        # Filtrer les données pour la période spécifiée
        filtered_data_le_8 = [(ts, tt, pf, ep) for ts, tt, pf, ep in zip(timestamps_le_8, time_taken_le_8, proofs_found_le_8, eligible_plots_le_8) if ts >= start_time and pf > 0]
        filtered_data_gt_8 = [(ts, tt, pf, ep) for ts, tt, pf, ep in zip(timestamps_gt_8, time_taken_gt_8, proofs_found_gt_8, eligible_plots_gt_8) if ts >= start_time and pf > 0]

        # Plot points where proofs_found_le_8 > 0
        scatter_le_8 = self.ax2.scatter([ts for ts, _, _, _ in filtered_data_le_8],
                                        [tt for _, tt, _, _ in filtered_data_le_8],
                                        color=color_blue, marker='o', label='<= 8 secondes')

        # Plot points where proofs_found_gt_8 > 0
        scatter_gt_8 = self.ax2.scatter([ts for ts, _, _, _ in filtered_data_gt_8],
                                        [tt for _, tt, _, _ in filtered_data_gt_8],
                                        color=color_red, marker='o', label='> 8 secondes')

        # Add background grid
        self.ax2.axhline(y=8, color=color_white, linestyle='--', linewidth=0.5)
        self.ax2.set_title('Temps des preuves trouvées sur la dernière heure', color=color_white)

        # Définir le format de l'axe x
        self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Hh%M'))
        self.ax2.set_xlim(start_time, end_time)

        # Calculer la limite maximale de l'axe Y
        time_taken_le_8_values = [tt for _, tt, _, _ in filtered_data_le_8]
        time_taken_gt_8_values = [tt for _, tt, _, _ in filtered_data_gt_8]

        max_time_taken = max(max(time_taken_le_8_values, default=0), max(time_taken_gt_8_values, default=0))
        y_upper_limit = max_time_taken + 2 if max_time_taken > 10 else 10
        self.ax2.set_ylim(0, y_upper_limit)

        # Utilisation de MaxNLocator pour limiter le nombre de ticks sur l'axe x
        self.ax2.xaxis.set_major_locator(ticker.MaxNLocator(20))
        self.fig2.autofmt_xdate()

        # Gestion du curseur
        if self.cursor2:
            self.cursor2.visible = False

        self.cursor2 = mplcursors.cursor([scatter_le_8, scatter_gt_8], hover=True)

        @self.cursor2.connect("add")
        def on_add_cursor2(sel):
            tooltip_color = color_white
            face_color = color_black
            artist = sel.artist

            if artist == scatter_le_8:
                index = sel.index
                if 0 <= index < len(filtered_data_le_8):
                    ts, tt, pf, ep = filtered_data_le_8[index]
                    timestamp_le_8 = ts.strftime('%d-%m-%Y %H:%M:%S')
                    sel.annotation.set(text=f"{timestamp_le_8}\n"
                                            f"Parcelles éligibles: {ep}\n"
                                            f"Preuves trouvées: {pf}\n"
                                            f"Temps: {tt:.2f}",
                                       color=tooltip_color,
                                       bbox=dict(facecolor=face_color, edgecolor='none'),
                                       ha='left')

            elif artist == scatter_gt_8:
                index = sel.index
                if 0 <= index < len(filtered_data_gt_8):
                    ts, tt, pf, ep = filtered_data_gt_8[index]
                    timestamp_gt_8 = ts.strftime('%d-%m-%Y %H:%M:%S')
                    sel.annotation.set(text=f"{timestamp_gt_8}\n"
                                            f"Parcelles éligibles: {ep}\n"
                                            f"Preuves trouvées: {pf}\n"
                                            f"Temps: {tt:.2f}",
                                       color=tooltip_color,
                                       bbox=dict(facecolor=face_color, edgecolor='none'),
                                       ha='left')

        # Mettre à jour le canevas
        self.canvas2.draw()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def close_app(self):
        self.root.quit()
        self.root.destroy()


def main():
    root = tk.Tk()
    LogMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
