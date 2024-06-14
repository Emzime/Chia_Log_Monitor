@echo off
cd /d %~dp0

:: Définir le titre de la fenêtre
title Starting Chia Monitor

:: Lancer Python dans une nouvelle fenêtre
:: start "Starting Chia Monitor" python chia_log_monitor.py
start "Starting Chia Monitor" /min python Run.py
