import datetime
import re
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog, Scrollbar, Text

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

log_pattern = re.compile(
    r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}) harvester chia\.harvester\.harvester: INFO\s+(\d+) plots were eligible for farming \w+\.\.\. Found (\d+) proofs\. Time: ([\d.]+) s\. Total (\d+) plots')
log_data = defaultdict(list)
default_log_file = r'\\VM-CHIA\ChiaLog\debug.log'


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


def calculate_summary_stats():
    if not log_data['timestamp']:
        return "No log data found."

    total_entries = len(log_data['timestamp'])
    avg_time_taken = sum(log_data['time_taken']) / total_entries
    min_time_taken = min(log_data['time_taken'])
    max_time_taken = max(log_data['time_taken'])
    total_proofs_found = sum(log_data['proofs_found'])

    summary_stats = (
        f"=[ Statistiques ]=\n"
        f"Total des entrées: {total_entries}\n"
        f"Total des preuves trouvées: {total_proofs_found}\n"
        f"Durée minimale: {min_time_taken:.2f} secondes\n"
        f"Temps moyen: {avg_time_taken:.2f} secondes\n"
        f"Temps maximum: {max_time_taken:.2f} secondes\n\n"
    )

    return summary_stats


class LogMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chia Log Monitor")
        self.center_window(1400, 600)

        self.frame = tk.Frame(root)
        self.frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)

        self.load_button = tk.Button(self.frame, text="Load Log File", command=self.load_log_file)
        self.load_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.N)

        self.top_frame = tk.Frame(self.frame)
        self.top_frame.grid(row=1, column=0, sticky=tk.NSEW)

        self.summary_frame = tk.Frame(self.top_frame, bd=2, relief=tk.SUNKEN)
        self.summary_frame.grid(row=0, column=0, padx=5, pady=10, sticky=tk.NSEW)

        self.summary_text = Text(self.summary_frame, wrap=tk.WORD, height=10)
        self.summary_text.grid(row=0, column=0, sticky=tk.NSEW)

        self.summary_scrollbar = Scrollbar(self.summary_frame, orient=tk.VERTICAL, command=self.summary_text.yview)
        self.summary_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.summary_text.configure(yscrollcommand=self.summary_scrollbar.set)

        self.stats_frame = tk.Frame(self.top_frame, bd=2, relief=tk.SUNKEN)
        self.stats_frame.grid(row=0, column=1, padx=5, pady=10, sticky=tk.NSEW)

        self.stats_text = Text(self.stats_frame, wrap=tk.WORD, height=10)
        self.stats_text.grid(row=0, column=0, sticky=tk.NSEW)

        self.stats_scrollbar = Scrollbar(self.stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.stats_text.configure(yscrollcommand=self.stats_scrollbar.set)

        self.bottom_frame = tk.Frame(root)
        self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)

        self.plot_frame1 = tk.Frame(self.bottom_frame, bd=2, relief=tk.SUNKEN)
        self.plot_frame1.grid(row=0, column=0, padx=5, pady=10, sticky=tk.NSEW)

        self.plot_frame2 = tk.Frame(self.bottom_frame, bd=2, relief=tk.SUNKEN)
        self.plot_frame2.grid(row=0, column=1, padx=5, pady=10, sticky=tk.NSEW)

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
        self.plot_frame2.grid_rowconfigure(0, weight=1)
        self.plot_frame2.grid_columnconfigure(0, weight=1)

        # Create figure and axis instances
        self.fig1, self.ax1 = plt.subplots(figsize=(8, 6))
        self.fig2, self.ax2 = plt.subplots(figsize=(8, 6))

        # Create canvas instances and grid them
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.plot_frame1)
        self.canvas1.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.plot_frame2)
        self.canvas2.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)

        self.maximize_window()

        # Load default log file and start periodic update
        self.load_default_log_file()
        self.update_periodically()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def load_log_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            read_log_file(file_path)
            self.update_ui()

    def load_default_log_file(self):
        if default_log_file:
            try:
                read_log_file(default_log_file)
                self.update_ui()
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
        self.root.after(2000, self.update_periodically)

    def update_ui(self):
        summary = print_summary()
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        self.summary_text.see(tk.END)  # Fait défiler jusqu'à la fin

        stats = calculate_summary_stats()
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats)
        self.stats_text.see(tk.END)  # Fait défiler jusqu'à la fin

        self.plot_data()

    def plot_data(self):
        if not log_data['timestamp']:
            return

        # Calculer l'heure actuelle moins une heure
        now = datetime.datetime.now()
        start_time = now - datetime.timedelta(hours=1)

        # Filtrer les données pour ne garder que celles dans l'intervalle de la dernière heure
        filtered_timestamps = []
        filtered_time_taken = []
        filtered_proofs_found = []

        for timestamp, time_taken, proofs_found in zip(log_data['timestamp'], log_data['time_taken'], log_data['proofs_found']):
            if timestamp >= start_time:
                filtered_timestamps.append(timestamp)
                filtered_time_taken.append(time_taken)
                filtered_proofs_found.append(proofs_found)

        # Efface les tracés précédents
        self.ax1.clear()
        self.ax2.clear()

        # Met à jour les données dans les tracés existants
        self.ax1.plot(filtered_timestamps, filtered_time_taken)
        self.ax1.set_title('Temps en secondes sur la dernière heure')
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Hh%M'))
        self.ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))  # Intervalles de 10 minutes
        self.fig1.autofmt_xdate()

        self.ax2.plot(filtered_timestamps, filtered_proofs_found)
        self.ax2.set_title('Preuves trouvées sur la dernière heure')
        self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Hh%M'))
        self.ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))  # Intervalles de 10 minutes
        self.fig2.autofmt_xdate()

        # Redessine le canevas
        self.canvas1.draw()
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
