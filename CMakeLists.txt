cmake_minimum_required(VERSION 3.12)
project(ChiaLogMonitor)

# Trouver Python3
find_package(Python3 REQUIRED COMPONENTS Interpreter)

# Trouver l'exécutable PyInstaller
execute_process(
    COMMAND ${Python3_EXECUTABLE} -m pip show pyinstaller
    OUTPUT_VARIABLE PYINSTALLER_INFO
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
if(NOT PYINSTALLER_INFO)
    message(FATAL_ERROR "PyInstaller n'est pas installé. Veuillez installer PyInstaller avec pip.")
endif()

# Extraire le chemin de l'exécutable PyInstaller
string(REGEX MATCH "Location: (.*)" _ ${PYINSTALLER_INFO})
set(PYINSTALLER_DIR ${CMAKE_MATCH_1})
set(PYINSTALLER_EXECUTABLE "${PYINSTALLER_DIR}/Scripts/pyinstaller.exe")

# Définir les arguments PyInstaller pour la version autonome
set(PYINSTALLER_ARGS_AUTONOME
  "--noconfirm"
  "--onefile"
  "--windowed"
  "--icon=${CMAKE_SOURCE_DIR}/images/icon.ico"
  "--add-data=${CMAKE_SOURCE_DIR}/images:images"
  "--add-binary=${CMAKE_SOURCE_DIR}/.venv/Lib/site-packages/matplotlib:matplotlib"
  "--add-binary=${CMAKE_SOURCE_DIR}/.venv/Lib/site-packages/mplcursors:mplcursors"
  "--hidden-import=matplotlib"
  "--hidden-import=mplcursors"
  "--hidden-import=platform"
  "--hidden-import=threading"
  "--hidden-import=tkinter"
  "--hidden-import=collections"
  "--hidden-import=datetime"
  "--hidden-import=tkinter.messagebox"
  "--hidden-import=tkinter.ttk"
  "--hidden-import=tkinter.filedialog"
  "--hidden-import=matplotlib.dates"
  "--hidden-import=matplotlib.pyplot"
  "--hidden-import=matplotlib.ticker"
  "--hidden-import=matplotlib.backends.backend_tkagg"
  "${CMAKE_SOURCE_DIR}/Chia_Log_Monitor.py"
  "--distpath=${CMAKE_BINARY_DIR}/dist/Chia Log Monitor Autonome"
)

# Définir les arguments PyInstaller pour la version non autonome
set(PYINSTALLER_ARGS_NON_AUTONOME
  "--noconfirm"
  "--windowed"
  "--icon=${CMAKE_SOURCE_DIR}/images/icon.ico"
  "--add-data=${CMAKE_SOURCE_DIR}/images:images"
  "--add-binary=${CMAKE_SOURCE_DIR}/.venv/Lib/site-packages/matplotlib:matplotlib"
  "--add-binary=${CMAKE_SOURCE_DIR}/.venv/Lib/site-packages/mplcursors:mplcursors"
  "--hidden-import=matplotlib"
  "--hidden-import=mplcursors"
  "--hidden-import=platform"
  "--hidden-import=threading"
  "--hidden-import=tkinter"
  "--hidden-import=collections"
  "--hidden-import=datetime"
  "--hidden-import=tkinter.messagebox"
  "--hidden-import=tkinter.ttk"
  "--hidden-import=tkinter.filedialog"
  "--hidden-import=matplotlib.dates"
  "--hidden-import=matplotlib.pyplot"
  "--hidden-import=matplotlib.ticker"
  "--hidden-import=matplotlib.backends.backend_tkagg"
  "${CMAKE_SOURCE_DIR}/Chia_Log_Monitor.py"
)

# Ajouter une cible personnalisée pour PyInstaller (version autonome)
add_custom_target(ChiaLogMonitorAutonome ALL
  COMMAND ${Python3_EXECUTABLE} -m PyInstaller ${PYINSTALLER_ARGS_AUTONOME}
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
  COMMENT "Packaging autonome avec PyInstaller"
)

# Ajouter une cible personnalisée pour PyInstaller (version non autonome)
add_custom_target(ChiaLogMonitorNonAutonome ALL
  COMMAND ${Python3_EXECUTABLE} -m PyInstaller ${PYINSTALLER_ARGS_NON_AUTONOME}
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
  COMMENT "Packaging non autonome avec PyInstaller"
)
