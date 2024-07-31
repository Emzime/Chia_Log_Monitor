@echo off
cd /d %~dp0

:: Définir le titre de la fenêtre
title Starting Chia Monitor

:: Lancer Python dans une nouvelle fenêtre
start "Starting Chia Monitor" python Chia_Log_Monitor.py
