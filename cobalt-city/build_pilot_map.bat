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

echo [1/6] Checking Python...
py --version
if errorlevel 1 goto failed

echo.
echo [2/6] Installing required package...
py -m pip install --upgrade pip
if errorlevel 1 goto failed
py -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo.
echo [3/6] Downloading the compact central Los Angeles pilot area...
py tools\fetch_osm.py
if errorlevel 1 goto failed

echo.
echo [4/6] Converting and validating map geometry...
py tools\build_geojson.py
if errorlevel 1 goto failed
py tools\validate_data.py
if errorlevel 1 goto failed

echo.
echo [5/6] Exporting Roblox chunks...
py tools\export_roblox_modules.py
if errorlevel 1 goto failed

echo.
echo [6/6] Packaging all ModuleScripts into one Roblox model...
py tools\build_roblox_model.py
if errorlevel 1 goto failed

echo.
echo ==========================================
echo BUILD COMPLETE
echo Roblox import file: roblox\CobaltCityData.rbxmx
echo Individual modules: roblox\ModuleScripts
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
