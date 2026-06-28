# Auto Stock Scanner

A Tkinter-based stock scanning app that fetches stock scan data, stores results in SQLite, and supports filtering and export.

## Features
- Fetch and update scan data from configured stock scan URLs
- Store results locally in SQLite
- Filter by file, date, column, and numeric thresholds
- Export filtered data to Excel
- Package as a Windows desktop app with PyInstaller

## Requirements
```bash
pip install pandas requests beautifulsoup4 ttkbootstrap
```

## Run locally
```bash
python app_github.py
```

## Build Windows EXE
```bash
python -m PyInstaller --onefile -w app_github.py
```
