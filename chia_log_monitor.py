import datetime
import re
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog, Scrollbar, Text

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import mplcursors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Chemin du log par défaut
default_log_file = r'\\VM-CHIA\ChiaLog\debug.log'

log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}) harvester chia\.harvester\.harvester: INFO\s+(\d+) plots were eligible for farming \w+\.\.\. Found (\d+) proofs\. Time: ([\d.]+) s\. Total (\d+) plots')
pool_info_pattern = re.compile(r"GET /pool_info response: ({.*})")
farmer_info_pattern = re.compile(r"GET /farmer response: ({.*})")
giga_horse_fee_pattern = re.compile(r"Found proof: .* used_gpu = (?P<used_gpu>True|False), fee_rate = (?P<fee_rate>\d+\.\d+) %")
points_pattern = re.compile(r"Points: (\d+)")

log_data = defaultdict(list)
pool_info = {}
farmer_info = {}


def read_log_file(file_path):
    log_data.clear()
    with open(file_path, 'r') as file:
        for line in file:
            parsed_line = parse_log_line(line)
            if parsed_line:
                timestamp, eligible_plots, proofs_found, time_taken, total_plots = parsed_line
                log_data['timestamp'].append(timestamp)
                log_data['eligible_plots'].append(eligible_plots)
                log_data['proofs_found'].append(proofs_found)
                log_data['time_taken'].append(time_taken)
                log_data['total_plots'].append(total_plots)
            else:
                parse_pool_info(line)
                parse_farmer_info(line)
                parse_points(line)
                if "Found proof" in line:
                    if 'giga_horse_info' not in log_data:
                        log_data['giga_horse_info'] = []
                    log_data['giga_horse_info'].append(line)


def parse_log_line(line):
    match = log_pattern.match(line)
    if match:
        timestamp_str = match.group(1)
        timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
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
                return info.get('used_gpu') == 'True', float(info.get('fee_rate'))
    return False, None


def parse_points(line):
    match = points_pattern.search(line)
    if match:
        points = int(match.group(1))
        log_data['points'].append(points)
        return True
    return False


def print_summary():
    total_entries = len(log_data['timestamp'])
    if total_entries == 0:
        return "No log data found."

    detailed_summary = "Detailed log summary:\n"
    for i in range(total_entries):
        detailed_summary += (f"{log_data['timestamp'][i]} - Eligible Plots: {log_data['eligible_plots'][i]}, "
                             f"Proofs Found: {log_data['proofs_found'][i]}, "
                             f"Time Taken: {log_data['time_taken'][i]:.2f} s, "
                             f"Total Plots: {log_data['total_plots'][i]}\n")

    return detailed_summary


def print_summary_stats():
    if not log_data['timestamp']:
        return "No log data found."

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
    gpu_used, fee_rate = parse_giga_horse_info(log_data['giga_horse_info'])
    gpu_used = "Oui" if gpu_used else "Non"
    fee_rate = fee_rate if fee_rate else "Données en attentes"

    # Affiche l'heure de la dernière mise à jour
    last_update_time = datetime.datetime.now().strftime('%H:%M:%S')

    # Affiche l'heure de la dernière preuve <= 8 sec
    last_proof_le_8_time = "Aucunes preuves inférieurs à 8 sec trouvée"
    if total_proofs_found > 0:
        last_proof_le_8_indices = [
            i for i, (proof, time_taken) in enumerate(zip(log_data['proofs_found'], log_data['time_taken']))
            if proof > 0 and time_taken <= 8
        ]
        if last_proof_le_8_indices:
            last_proof_le_8_day = log_data['timestamp'][last_proof_le_8_indices[-1]].strftime('%d/%m/%Y')
            last_proof_le_8_time = log_data['timestamp'][last_proof_le_8_indices[-1]].strftime('%H heures %M minutes %S secondes')
            last_proof_le_8_time = f"Dernière preuve inférieur à 8 sec trouvée le {last_proof_le_8_day} à {last_proof_le_8_time}"

    # Affiche l'heure de la dernière preuve > 8 sec
    last_proof_gt_8_time = "Aucunes preuves supérieures à 8 sec trouvée"
    if total_proofs_found > 0:
        last_proof_gt_8_indices = [
            i for i, (proof, time_taken) in enumerate(zip(log_data['proofs_found'], log_data['time_taken']))
            if proof > 0 and time_taken > 8
        ]
        if last_proof_gt_8_indices:
            last_proof_gt_8_day = log_data['timestamp'][last_proof_gt_8_indices[-1]].strftime('%d/%m/%Y')
            last_proof_gt_8_time = log_data['timestamp'][last_proof_gt_8_indices[-1]].strftime('%H heures %M minutes %S secondes')
            last_proof_gt_8_time = f"Dernière preuve supérieur à 8 sec trouvée le {last_proof_gt_8_day} à {last_proof_gt_8_time}"

    # Crée l'affichage des statistiques
    summary_stats = (
        f"Dernière mise à jour: {last_update_time}\n\n"
        ":: Infos sur la pool ::\n"
        f" Nom: {pool_name}\n"
        f" Discord: {pool_discord}\n"
        f" Fee: {pool_fee}%\n"

        "\n:: Infos sur la ferme ::\n"
        f" Utilisation du GPU: {gpu_used}\n"
        f" Total de parcelles: {total_plots}\n"
        f" Difficulté de la ferme: {current_difficulty}\n"
        f" Points de la ferme: {current_points}\n"

        "\n:: Infos sur les preuves ::\n"
        f" Total des entrées: {total_entries}\n"
        f" Total des preuves trouvées: {total_proofs_found}\n"
        f" {last_proof_le_8_time}\n"
        f" {last_proof_gt_8_time}\n\n"
        f" Temps minimal des preuves: {min_proof_time:.2f} secondes\n"
        f" Temps moyen des preuves: {avg_proof_time:.2f} secondes\n"
        f" Temps maximal des preuves: {max_proof_time:.2f} secondes\n\n"
        f" {proof_info_le_8}"
        f" {proof_info_gt_8}"

        "\n:: Autres données ::\n"
        f" GigaHorse Fee: {fee_rate}%\n"
        f" Temps écoulé depuis le début du log: {elapsed_time_formatted}\n"
    )

    return summary_stats


def calculate_proof_times(time_taken_list):
    if not time_taken_list:
        return 0.0, 0.0, 0.0
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

    proof_info_le_8 = f"Total de preuves inférieures à 8 secondes: {total_count_le_8} ({proof_percentage_le_8:.2f}%)\n"
    proof_info_gt_8 = f"Total de preuves supérieures à 8 secondes: {total_count_gt_8} ({proof_percentage_gt_8:.2f}%)\n"

    return proof_info_le_8, proof_info_gt_8


def calculate_elapsed_time():
    first_timestamp = log_data['timestamp'][0]
    last_timestamp = log_data['timestamp'][-1]
    elapsed_time = last_timestamp - first_timestamp
    return format_elapsed_time(elapsed_time)


def extract_pool_info():
    pool_name = pool_info.get('name', 'N/A')
    pool_discord = pool_info.get('discord', 'N/A')
    pool_fee = pool_info.get('fee', 'N/A')
    return pool_name, pool_discord, pool_fee


def extract_farmer_info():
    current_difficulty = farmer_info.get('current_difficulty', 'N/A')
    current_points = farmer_info.get('current_points', 'N/A')
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


class LogMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chia Log Monitor")
        self.center_window(1400, 600)

        # Set dark background for the root window
        self.root.configure(bg='#2E2E2E')

        self.frame = tk.Frame(root, bg='#2E2E2E')
        self.frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)

        self.load_button = tk.Button(self.frame, text="Charger le fichier de logs", command=self.load_log_file, bg='#999999', fg='#000000')
        self.load_button.grid(row=0, column=0, columnspan=2, padx=10, pady=(20, 0), sticky=tk.N)

        self.top_frame = tk.Frame(self.frame, bg='#2E2E2E')
        self.top_frame.grid(row=1, column=0, sticky=tk.NSEW)

        self.summary_frame = tk.Frame(self.top_frame, bd=2, relief=tk.SUNKEN, bg='#333333')
        self.summary_frame.grid(row=0, column=0, padx=5, pady=(10, 5), sticky=tk.NSEW)

        self.summary_text = Text(self.summary_frame, wrap=tk.WORD, height=30, bg='#333333', fg='white')
        self.summary_text.grid(row=0, column=0, sticky=tk.NSEW)

        self.summary_scrollbar = Scrollbar(self.summary_frame, orient=tk.VERTICAL, command=self.summary_text.yview, activebackground='#666666')
        self.summary_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.summary_text.configure(yscrollcommand=self.summary_scrollbar.set, padx=10, pady=5)

        self.stats_frame = tk.Frame(self.top_frame, bd=2, relief=tk.SUNKEN, bg='#333333')
        self.stats_frame.grid(row=0, column=1, padx=5, pady=(10, 5), sticky=tk.NSEW)

        self.stats_text = Text(self.stats_frame, wrap=tk.WORD, height=30, bg='#333333', fg='white')
        self.stats_text.grid(row=0, column=0, sticky=tk.NSEW)

        self.stats_scrollbar = Scrollbar(self.stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview, activebackground='#666666')
        self.stats_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.stats_text.configure(yscrollcommand=self.stats_scrollbar.set, padx=10, pady=5)

        self.bottom_frame = tk.Frame(root, bg='#2E2E2E')
        self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)

        self.plot_frame1 = tk.Frame(self.bottom_frame, bd=2, relief=tk.SUNKEN, bg='#333333')
        self.plot_frame1.grid(row=0, column=0, padx=5, pady=(5, 10), sticky=tk.NSEW)

        self.plot_frame1_scrollbar = Scrollbar(self.plot_frame1, orient=tk.VERTICAL, activebackground='#666666')
        self.plot_frame1_scrollbar.grid(row=0, column=1, sticky=tk.NS)

        self.plot_frame2 = tk.Frame(self.bottom_frame, bd=2, relief=tk.SUNKEN, bg='#333333')
        self.plot_frame2.grid(row=0, column=1, padx=5, pady=(5, 10), sticky=tk.NSEW)

        self.plot_frame2_scrollbar = Scrollbar(self.plot_frame2, orient=tk.VERTICAL, activebackground='#666666')
        self.plot_frame2_scrollbar.grid(row=0, column=1, sticky=tk.NS)

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

        self.maximize_window()

        # Initialize cursor attributes
        self.cursor1 = None
        self.cursor2 = None

        # Load default log file and start periodic update
        self.load_default_log_file()
        self.update_periodically()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    @staticmethod
    def load_log_file():
        file_path = filedialog.askopenfilename(filetypes=[("Log Files", "*.log"), ("All Files", "*.*")])
        if file_path:
            read_log_file(file_path)

    @staticmethod
    def load_default_log_file():
        if default_log_file:
            try:
                read_log_file(default_log_file)
            except FileNotFoundError:
                print(f"Default log file '{default_log_file}' not found.")

    def update_periodically(self):
        if default_log_file:
            try:
                self.load_default_log_file()
            except FileNotFoundError:
                print(f"Default log file '{default_log_file}' not found.")
        else:
            try:
                self.load_log_file()
            except FileNotFoundError:
                print(f"Selected log file not found.")

        self.update_ui()
        self.root.after(5000, self.update_periodically)

    def update_ui(self):
        summary = print_summary()
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        self.summary_text.see(tk.END)

        stats = print_summary_stats()
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats)
        self.stats_text.see(tk.END)

        if not log_data['timestamp']:
            # Cacher le top_frame
            self.top_frame.grid_forget()
            # Cacher le bottom_frame
            self.bottom_frame.grid_forget()

            # Afficher un message à la place dans summary_text
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, "Aucune donnée de log disponible.")
            self.summary_text.see(tk.END)
        else:
            self.top_frame.grid(row=1, column=0, sticky=tk.NSEW)  # Afficher le top_frame
            self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)  # Afficher le bottom_frame

        self.plot_data()

    def plot_data(self):
        if not log_data['timestamp']:
            return

        # Calculer l'heure actuelle moins une heure
        now = datetime.datetime.now()
        start_time = now - datetime.timedelta(minutes=60)

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

        # Plot pour <= 8 secondes avec des marqueurs 'o'
        self.ax1.plot(timestamps_le_8, time_taken_le_8, color='#17D283', marker='o', markersize=5, linestyle='-', label='<= 8 secondes')

        # Plot pour > 8 secondes avec des marqueurs 'o'
        self.ax1.plot(timestamps_gt_8, time_taken_gt_8, color='#FF4500', marker='o', markersize=5, linestyle='None', label='> 8 secondes')

        # Colorer les points où proofs_found_le_8 > 0
        for x, y, proof in zip(timestamps_le_8, time_taken_le_8, proofs_found_le_8):
            if proof > 0:
                self.ax1.plot(x, y, color='#5385F6', marker='o', markersize=5, linestyle='None')

        # Colorer les points où proofs_found_gt_8 > 0
        for x, y, proof in zip(timestamps_gt_8, time_taken_gt_8, proofs_found_gt_8):
            if proof > 0:
                self.ax1.plot(x, y, color='#5385F6', marker='o', markersize=5, linestyle='None')

        # Configurer le reste du graphique
        self.ax1.axhline(y=8, color='white', linestyle='--', linewidth=0.5)
        self.ax1.set_title('Temps de toutes les preuves sur la dernière heure', color='white')
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Hh%M'))
        self.ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
        self.fig1.autofmt_xdate()

        # Définir les couleurs pour un thème foncé
        self.fig1.patch.set_facecolor('#333333')
        self.ax1.set_facecolor('#333333')
        self.ax1.tick_params(axis='x', colors='white')
        self.ax1.tick_params(axis='y', colors='white')
        self.ax1.spines['bottom'].set_color('white')
        self.ax1.spines['top'].set_color('white')
        self.ax1.spines['left'].set_color('white')
        self.ax1.spines['right'].set_color('white')
        self.ax1.title.set_color('white')
        self.ax1.xaxis.label.set_color('white')
        self.ax1.yaxis.label.set_color('white')

        # Gérer les tooltips avec mplcursors sur self.ax1
        if self.cursor1:
            self.cursor1.visible = False

        self.cursor1 = mplcursors.cursor(self.ax1, hover=True)

        @self.cursor1.connect("add")
        def on_add_cursor1(sel, tooltip_color='white', face_color='black'):
            idx = int(sel.index)

            if idx < len(timestamps_gt_8):
                timestamp_gt_8 = timestamps_gt_8[idx]
                parcelles = eligible_plots_gt_8[idx]
                temps = time_taken_gt_8[idx]
                sel.annotation.set(text=f"{timestamp_gt_8.strftime('%d-%m-%Y %H:%M:%S')}\n"
                                        f"Parcelles éligibles: {parcelles}\n"
                                        f"Preuves trouvées: {proofs_found_gt_8[idx]}\n"
                                        f"Temps: {temps:.2f} s",
                                   color=tooltip_color,
                                   bbox=dict(facecolor=face_color, edgecolor='none'),
                                   ha='left')
            elif idx - len(timestamps_gt_8) < len(timestamps_le_8):
                timestamp_le_8 = timestamps_le_8[idx]
                parcelles = eligible_plots_le_8[idx]
                temps = time_taken_le_8[idx]
                sel.annotation.set(text=f"{timestamp_le_8.strftime('%d-%m-%Y %H:%M:%S')}\n"
                                        f"Parcelles éligibles: {parcelles}\n"
                                        f"Preuves trouvées: {proofs_found_le_8[idx]}\n"
                                        f"Temps: {temps:.2f} s",
                                   color=tooltip_color,
                                   bbox=dict(facecolor=face_color, edgecolor='none'),
                                   ha='left')
            else:
                sel.annotation.set(text="Aucune donnée disponible",
                                   color=tooltip_color,
                                   bbox=dict(facecolor=face_color, edgecolor='none'),
                                   ha='left')

        # Redessine le canevas
        self.canvas1.draw()

    def found_proof_graphs(self, timestamps_le_8, time_taken_le_8, eligible_plots_le_8, proofs_found_le_8, timestamps_gt_8, time_taken_gt_8, eligible_plots_gt_8, proofs_found_gt_8):
        # Efface les tracés précédents
        self.ax2.cla()

        # Déterminer le début et la fin de la période à afficher
        # Fin à l'instant actuel
        end_time = datetime.datetime.now()
        # Début il y a 30 minutes
        start_time = end_time - datetime.timedelta(minutes=60)

        # Tracer les données filtrées
        self.ax2.plot(timestamps_le_8, proofs_found_le_8, color='#17D283', marker='o', markersize=4, linestyle='-', label='<= 8 secondes')
        self.ax2.plot(timestamps_gt_8, proofs_found_gt_8, color='#FF4500', marker='o', markersize=4, linestyle='-', label='> 8 secondes')

        # Configurer le titre et les étiquettes de l'axe
        self.ax2.set_title('Temps des preuves trouvées sur la dernière heure', color='white')
        self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Hh%M'))
        self.ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
        self.ax2.yaxis.set_major_locator(plt.MultipleLocator(1))
        # self.ax2.legend(loc='upper left')

        # Incline les étiquettes de l'axe X à 45 degrés
        plt.setp(self.ax2.get_xticklabels(), rotation=45, ha='right')

        # Configurer le style du graphique
        self.fig2.patch.set_facecolor('#333333')
        self.ax2.set_facecolor('#333333')
        self.ax2.tick_params(axis='x', colors='white')
        self.ax2.tick_params(axis='y', colors='white')
        self.ax2.spines['bottom'].set_color('white')
        self.ax2.spines['top'].set_color('white')
        self.ax2.spines['left'].set_color('white')
        self.ax2.spines['right'].set_color('white')
        self.ax2.title.set_color('white')
        self.ax2.xaxis.label.set_color('white')
        self.ax2.yaxis.label.set_color('white')

        # Calculer la limite maximale de l'axe Y basée sur proofs_found_gt_8
        max_proof_found = max(proofs_found_gt_8, default=0)
        y_upper_limit = max(5, max_proof_found)
        self.ax2.set_ylim(0, y_upper_limit)
        self.ax2.set_xlim(start_time, end_time)

        # Ajouter le quadrillage à l'arrière-plan
        self.ax2.grid(True, color='grey', linestyle='--', linewidth=0.5)

        # Gestion du curseur
        if self.cursor2:
            self.cursor2.visible = False

        self.cursor2 = mplcursors.cursor(self.ax2, hover=True)

        @self.cursor2.connect("add")
        def on_add_cursor2(sel, tooltip_color='white', face_color='black'):
            idx = int(sel.index)  # Utilisation de sel.index au lieu de sel.target.index

            if sel.artist.get_label() == '<= 8 secondes':
                if idx < len(proofs_found_le_8):
                    timestamp_le_8 = timestamps_le_8[idx].strftime('%d-%m-%Y %H:%M:%S')
                    sel.annotation.set(text=f"{timestamp_le_8}\n"
                                            f"Parcelles éligibles: {eligible_plots_le_8[idx]}\n"
                                            f"Preuves trouvées: {proofs_found_le_8[idx]}\n"
                                            f"Temps: {time_taken_le_8[idx]:.2f}",
                                       color=tooltip_color,
                                       bbox=dict(facecolor=face_color, edgecolor='none'),
                                       ha='left')
            elif sel.artist.get_label() == '> 8 secondes':
                idx -= len(proofs_found_le_8)
                if idx < len(proofs_found_gt_8):
                    timestamp_gt_8 = timestamps_gt_8[idx].strftime('%d-%m-%Y %H:%M:%S')
                    sel.annotation.set(text=f"{timestamp_gt_8}\n"
                                            f"Parcelles éligibles: {eligible_plots_gt_8[idx]}\n"
                                            f"Preuves trouvées: {proofs_found_gt_8[idx]}\n"
                                            f"Temps: {time_taken_gt_8[idx]:.2f}",
                                       color=tooltip_color,
                                       bbox=dict(facecolor=face_color, edgecolor='none'),
                                       ha='left')
            else:
                sel.annotation.set(text="Aucune donnée disponible",
                                   color=tooltip_color,
                                   bbox=dict(facecolor=face_color, edgecolor='none'),
                                   ha='left')

        # Mettre à jour le canevas
        self.canvas2.draw()

    def maximize_window(self):
        self.root.state('zoomed')
        self.root.attributes('-topmost', False)

    def close_app(self):
        self.root.quit()
        self.root.destroy()


def main():
    root = tk.Tk()
    LogMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
