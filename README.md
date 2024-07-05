
. ./venv/Scripts/activate
py Standalone_Builder.py


pyinstaller --noconfirm --onefile --windowed --icon "C:/PycharmProjects/Chia_Log_Monitor/images/icon.ico" --add-data "C:/PycharmProjects/Chia_Log_Monitor/images/icon.ico;images" --add-data "C:/PycharmProjects/Chia_Log_Monitor/images;images" "C:/PycharmProjects/Chia_Log_Monitor/chia_log_monitor.py"

