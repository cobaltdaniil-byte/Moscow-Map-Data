@echo off
setlocal
cd /d "%~dp0"
title Cobalt City RP - Map Builder

echo ==========================================
echo   COBALT CITY RP - BUILD PILOT MAP
echo ==========================================
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or the py launcher is missing.
  echo Install Python 3 from https://www.python.org/downloads/
  echo During setup, enable "Add python.exe to PATH".
  pause
  exit /b 1
)

echo [1/5] Checking Python...
py --version
if errorlevel 1 goto failed

echo.
echo [2/5] Installing required package...
py -m pip install --upgrade pip
if errorlevel 1 goto failed
py -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo.
echo [3/5] Downloading the compact central Los Angeles pilot area...
py tools\fetch_osm.py
if errorlevel 1 goto failed

echo.
echo [4/5] Converting and validating map geometry...
py tools\build_geojson.py
if errorlevel 1 goto failed
py tools\validate_data.py
if errorlevel 1 goto failed

echo.
echo [5/5] Exporting Roblox chunks...
py tools\export_roblox_modules.py
if errorlevel 1 goto failed

echo.
echo ==========================================
echo BUILD COMPLETE
echo Files are in: roblox\ModuleScripts
echo Report: data\chunk_manifest.json
echo ==========================================
echo Do not delete or change any Moscow map files.
pause
exit /b 0

:failed
echo.
echo BUILD STOPPED. Read the error above and send it to ChatGPT.
pause
exit /b 1
