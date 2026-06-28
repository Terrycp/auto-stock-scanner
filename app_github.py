import time
import json
import os
import sys
from pathlib import Path

import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from io import StringIO
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as tb

# --- Global Config ---
current_df = pd.DataFrame()


def get_app_base_dir() -> Path:
    """Return a writable directory for runtime files.

    When launched from a PyInstaller one-file EXE, sys.executable points to the
    real executable in dist/, so writing there keeps the DB/settings persistent.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


DB_NAME = str(get_app_base_dir() / "stock_data.db")
SETTINGS_FILE = str(get_app_base_dir() / "app_settings.json")
URL_LIST = [
    ("Bullish Catapult", "https://stockcharts.com/def/servlet/SC.scan?s=TSAL[t.t_eq_s]![as0,20,tv_gt_40000]![ya_eq_1]&report=predefall"),
    ("Quadruple Top Breakout", "https://stockcharts.com/def/servlet/SC.scan?s=TSAL[t.t_eq_s]![as0,20,tv_gt_40000]![yj_eq_1]&report=predefall"),
    ("Morning Star", "https://stockcharts.com/def/servlet/SC.scan?s=TSAL[t.t_eq_s]![as0,20,tv_gt_40000]![wh_eq_1]&report=predefall"),
     ("Bear Trap", "https://stockcharts.com/def/servlet/SC.scan?scanId=pf-bear-trap&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Bearish Signal Reversal", "https://stockcharts.com/def/servlet/SC.scan?scanId=pf-bearish-signal-reversal&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Bullish Triangle", "https://stockcharts.com/def/servlet/SC.scan?scanId=pf-bullish-triangle&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Bullish Engulfing", "https://stockcharts.com/def/servlet/SC.scan?scanId=bullish-engulfing&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Three White Soldiers", "https://stockcharts.com/def/servlet/SC.scan?scanId=three-white-soldiers&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Bullish MACD Crossover", "https://stockcharts.com/def/servlet/SC.scan?scanId=bullish-macd-crossovers&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Oversold Improving RSI", "https://stockcharts.com/def/servlet/SC.scan?scanId=oversold-with-an-improving-rsi&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Piercing Line", "https://stockcharts.com/def/servlet/SC.scan?scanId=piercing-line&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Underperforming SPY 52W Low", "https://stockcharts.com/def/servlet/SC.scan?scanId=underperforming-spy-52-week-relative-lows&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Underperforming SPY 9M Low", "https://stockcharts.com/def/servlet/SC.scan?scanId=underperforming-spy-9-month-relative-lows&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("Underperforming SPY 6M Low", "https://stockcharts.com/def/servlet/SC.scan?scanId=underperforming-spy-6-month-relative-lows&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("New 52W Low", "https://stockcharts.com/def/servlet/SC.scan?scanId=new-52-week-lows&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("New 9M Low", "https://stockcharts.com/def/servlet/SC.scan?scanId=new-9-month-lows&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
    ("New 6M Low", "https://stockcharts.com/def/servlet/SC.scan?scanId=new-6-month-lows&filters=market-cap-greater-than-100m%2Cus-stocks&sorter=predefIntraday&rankby=true"),
]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
STANDARD_COLS = [
    "Symbol",
    "Name",
    "Exchange",
    "Sector",
    "Industry",
    "Last",
    "Volume",
    "SCTR",
    "U",
    "Daily MACD Line(12,26,9,Daily Close)",
    "Daily RSI(14,Daily Close)"
]
# Hard-coded GitHub token. Replace the value below with your personal access token.
# NOTE: Storing tokens in source code is insecure. Only hard-code for local/testing.
GITHUB_TOKEN = "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"
# --- Database Setup ---
def add_column_if_not_exists(db_name, table_name, column_name, column_type):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]

    if column_name not in columns:
        cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN "{column_name}" {column_type}')
        print(f"Added column: {column_name}")

    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        FileName TEXT,
        Symbol TEXT,
        Name TEXT,
        Exchange TEXT,
        Sector TEXT,
        Industry TEXT,
        Last REAL,
        Volume INTEGER,
        SCTR REAL,
        U TEXT,
        Date TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deleted_records (
        FileName TEXT,
        Symbol TEXT,
        Date TEXT,
        DeletedAt TEXT,
        UNIQUE(FileName, Symbol, Date)
    )
    """)
    conn.commit()
    conn.close()

def download_latest_data():
    """Download latest DB from GitHub and merge new symbols into existing local DB"""
    if is_loading:
        return

    start_loading()
    try:
        init_db()
        
        # Configure GitHub details
        GITHUB_OWNER = "Terrycp"
        GITHUB_REPO = "auto-stock-scanner"
        GITHUB_BRANCH = "main"
        db_filename = os.path.basename(DB_NAME)
        
        # Download latest DB from GitHub
        token = GITHUB_TOKEN
        if token:
            api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{db_filename}?ref={GITHUB_BRANCH}"
            headers_req = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3.raw"}
            print(f"Downloading latest database from GitHub (using token)...")
            response = requests.get(api_url, headers=headers_req, timeout=15)
        else:
            raw_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{db_filename}"
            print(f"Downloading latest database from GitHub (no token)...")
            response = requests.get(raw_url, headers=HEADERS, timeout=15)
        
        response.raise_for_status()
        
        # Save downloaded DB to temporary file
        temp_db_path = f"{DB_NAME}.temp"
        with open(temp_db_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded database successfully")
        
        # Open connections to both local and GitHub DBs
        local_conn = sqlite3.connect(DB_NAME)
        github_conn = sqlite3.connect(temp_db_path)

        try:
            # Read all data from GitHub DB
            github_df = pd.read_sql("SELECT * FROM stocks", github_conn)

            # 🔑 FILTER NEW SYMBOLS ONLY - Compare and find new records
            local_df = pd.read_sql("SELECT FileName, Symbol, Date FROM stocks", local_conn)
            deleted_df = pd.read_sql("SELECT FileName, Symbol, Date FROM deleted_records", local_conn)
            deleted_keys = set(zip(deleted_df["FileName"], deleted_df["Symbol"], deleted_df["Date"]))

            if len(local_df) > 0:
                local_keys = set(zip(local_df["FileName"], local_df["Symbol"], local_df["Date"]))
                local_df["Date"] = pd.to_datetime(local_df["Date"], errors="coerce")
                max_local_date = local_df["Date"].max()
                if pd.notna(max_local_date):
                    candidate_df = github_df[pd.to_datetime(github_df["Date"], errors="coerce") >= max_local_date].copy()
                else:
                    candidate_df = github_df.copy()

                new_records = candidate_df[candidate_df.apply(
                    lambda row: (row["FileName"], row["Symbol"], row["Date"]) not in local_keys
                                and (row["FileName"], row["Symbol"], row["Date"]) not in deleted_keys,
                    axis=1
                )]
            else:
                # Local DB is empty, all records from GitHub are new unless locally deleted
                new_records = github_df[github_df.apply(
                    lambda row: (row["FileName"], row["Symbol"], row["Date"]) not in deleted_keys,
                    axis=1
                )]

            if len(new_records) > 0:
                # Ensure DB has all columns first
                add_missing_columns_dynamic(new_records, "stocks")
                # Insert only new records
                new_records.to_sql("stocks", local_conn, if_exists="append", index=False)
                print(f"✅ Inserted {len(new_records)} new records from GitHub")
            else:
                print("✅ No new records found - local DB is up to date")
        finally:
            github_conn.close()
            local_conn.close()

        # Clean up temp file
        
        # Clean up temp file
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        print(f"✅ Download & Merge complete!")
        file_dropdown["values"] = get_file_names()
        load_data()
        
    except Exception as e:
        print(f"❌ Error downloading from GitHub: {e}")
        messagebox.showerror("Error", f"Failed to download from GitHub: {e}")
    
    stop_loading()

# --- Loading Function ---
is_loading = False  # flag to prevent multiple clicks

def start_loading():
    global is_loading
    is_loading = True
    fetch_btn.config(state="disabled")
    export_btn.config(state="disabled")
    progress_label.pack(pady=10)
    root.update()

def stop_loading():
    global is_loading
    is_loading = False
    fetch_btn.config(state="normal")
    export_btn.config(state="normal")
    progress_label.pack_forget()
    root.update()


# --- Scraping Function ---
def add_missing_columns_dynamic(df, table_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_cols = [row[1] for row in cursor.fetchall()]

    for col in df.columns:
        if col not in existing_cols:
            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN "{col}" TEXT')
            print(f"Added new column: {col}")

    conn.commit()
    conn.close()


def add_row():
    add_window = tk.Toplevel(root)
    add_window.title("Add Row")
    add_window.grab_set()

    entry_vars = {}
    field_names = [
        "FileName",
        "Symbol",
        "Name",
        "Exchange",
        "Sector",
        "Industry",
        "Last",
        "Volume",
        "SCTR",
        "U",
        "Daily MACD Line(12,26,9,Daily Close)",
        "Daily RSI(14,Daily Close)",
        "Date"
    ]

    for idx, field in enumerate(field_names):
        ttk.Label(add_window, text=field).grid(row=idx, column=0, padx=5, pady=4, sticky="w")
        entry_vars[field] = tk.StringVar()
        ttk.Entry(add_window, textvariable=entry_vars[field], width=40).grid(row=idx, column=1, padx=5, pady=4)

    def save_new_row():
        values = {field: var.get().strip() or None for field, var in entry_vars.items()}

        if not values["Symbol"]:
            messagebox.showwarning("Missing Symbol", "Please enter a Symbol.")
            return

        if not values["FileName"]:
            values["FileName"] = "Manual Entry"
        if not values["Date"]:
            values["Date"] = datetime.now().strftime("%Y-%m-%d")

        row_data = {k: v for k, v in values.items() if k != "Date" and k != "FileName"}
        row_data["FileName"] = values["FileName"]
        row_data["Date"] = values["Date"]

        df_insert = pd.DataFrame([row_data])
        add_missing_columns_dynamic(df_insert, "stocks")

        conn = sqlite3.connect(DB_NAME)
        df_insert.to_sql("stocks", conn, if_exists="append", index=False)
        conn.close()

        file_dropdown["values"] = get_file_names()
        load_data()
        add_window.destroy()

    ttk.Button(add_window, text="Save", command=save_new_row).grid(row=len(field_names), column=0, padx=5, pady=10)
    ttk.Button(add_window, text="Cancel", command=add_window.destroy).grid(row=len(field_names), column=1, padx=5, pady=10, sticky="e")


def delete_selected_rows():
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("No selection", "Please select one or more rows to delete.")
        return

    if not messagebox.askyesno("Confirm Delete", "Delete selected rows?"):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for item in selection:
        values = tree.item(item, "values")
        if not values:
            continue

        try:
            idx_file = cols.index("FileName")
            idx_symbol = cols.index("Symbol")
            idx_date = cols.index("Date")
        except ValueError:
            continue

        file_name = values[idx_file]
        symbol = values[idx_symbol]
        date_value = values[idx_date]

        cursor.execute(
            "INSERT OR IGNORE INTO deleted_records (FileName, Symbol, Date, DeletedAt) VALUES (?, ?, ?, datetime('now'))",
            (file_name, symbol, date_value)
        )
        cursor.execute(
            "DELETE FROM stocks WHERE FileName = ? AND Symbol = ? AND Date = ?",
            (file_name, symbol, date_value)
        )

    conn.commit()
    conn.close()
    load_data()


def fetch_data():
    """Alias for download_latest_data - Fetch & Update Data button now uses the new merge logic"""
    download_latest_data()

# --- Load Data into Table ---
def load_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM stocks", conn)
    conn.close()

    global cols
    cols = df.columns.tolist()

    # 🔥 Ensure Date is always last
    if "Date" in cols:
        cols.remove("Date")
        cols.append("Date")

    # Apply to treeview
    tree["columns"] = cols
    tree["displaycolumns"] = cols

    for col in cols:
        tree.heading(
            col,
            text=col,
            anchor="w",
            command=lambda c=col: sort_column(c, False)
        )
        tree.column(col, width=150, anchor="w", stretch=False)
    
    # Apply saved column widths
    apply_column_widths(saved_settings)

    refresh_table(df)
    update_date_filter(df)
    file_dropdown["values"] = get_file_names()

# --- Refresh Table in UI ---
def refresh_table(df):
    global current_df
    current_df = df.copy()

    total_label.config(text=f"Total records: {len(df)}")

    # --- Dynamic column ordering ---
    cols_order = list(df.columns)

    if "Date" in cols_order:
        cols_order.remove("Date")
        cols_order.append("Date")  # always last

    # ensure all columns exist
    for col in cols_order:
        if col not in df.columns:
            df[col] = None

    df = df[cols_order]

    # --- formatting ---
    display_df = df.copy()

    def format_numeric_value(x):
        if pd.isna(x) or (isinstance(x, str) and x.strip() == ""):
            return ""
        try:
            return f"{float(x):,.2f}"
        except (TypeError, ValueError):
            return x

    for col in [
        "Volume",
        "Last",
        "SCTR",
        "Daily MACD Line(12,26,9,Daily Close)",
        "Daily RSI(14,Daily Close)"
    ]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_numeric_value)

    # clear table
    for row in tree.get_children():
        tree.delete(row)

    # insert safely by column name
    for _, row in display_df.iterrows():
        tree.insert("", "end", values=[row[col] for col in cols_order])

# --- Update Date Dropdown ---
def update_date_filter(df):
    dates = sorted(df["Date"].unique(), reverse=True)
    date_dropdown["values"] = ["All"] + dates
    if date_filter.get() not in date_dropdown["values"]:
        date_filter.set("All")


# --- Filter by FileName, Columns, and Date ---
def apply_filter(*args):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM stocks WHERE 1=1"
    params = []

    if file_filter.get() != "All":
        query += " AND FileName = ?"
        params.append(file_filter.get())
    if search_col.get() != "All" and search_text.get():
        query += f" AND {search_col.get()} LIKE ?"
        params.append(f"%{search_text.get()}%")
    if date_filter.get() != "All":
        query += " AND Date = ?"
        params.append(date_filter.get())

    # --- Apply numeric filters (Last > 10, Volume > 1,000,000) ---
    query += " AND Last > ? AND Volume > ?"
    params.append(last_min.get())
    params.append(volume_min.get())

    df = pd.read_sql(query, conn, params=params)
    conn.close()

    refresh_table(df)

# --- Export to Excel ---
def export_excel():
    global current_df
    if current_df.empty:
        messagebox.showwarning("No Data", "No data to export! Please load or filter data first.")
        return
    
    # --- Format numbers with thousand separators ---
    df_export = current_df.copy()

    def format_numeric_value_export(x):
        if pd.isna(x) or (isinstance(x, str) and x.strip() == ""):
            return ""
        try:
            return f"{float(x):,.2f}"
        except (TypeError, ValueError):
            return x

    if "Volume" in df_export.columns:
        df_export["Volume"] = df_export["Volume"].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "")
    if "Last" in df_export.columns:
        df_export["Last"] = df_export["Last"].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
    if "SCTR" in df_export.columns:
        df_export["SCTR"] = df_export["SCTR"].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
    if "Daily MACD Line(12,26,9,Daily Close)" in df_export.columns:
        df_export["Daily MACD Line(12,26,9,Daily Close)"] = df_export["Daily MACD Line(12,26,9,Daily Close)"].apply(format_numeric_value_export)
    if "Daily RSI(14,Daily Close)" in df_export.columns:
        df_export["Daily RSI(14,Daily Close)"] = df_export["Daily RSI(14,Daily Close)"].apply(format_numeric_value_export)

    save_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx")],
        title="Save filtered data as Excel"
    )
    if save_path:
        df_export.to_excel(save_path, index=False)
        messagebox.showinfo("Exported", f"Data exported to {save_path}")

def sort_column(col, reverse):
    global current_df

    if current_df.empty:
        return

    sorted_df = current_df.copy()
    sorted_df[col] = pd.to_numeric(sorted_df[col], errors='ignore')
    sorted_df = sorted_df.sort_values(by=col, ascending=not reverse)

    refresh_table(sorted_df)

    # Add arrow indicator
    direction = " 🔽" if reverse else " 🔼"
    for c in cols:
        tree.heading(c, text=c)  # reset

    tree.heading(col, text=col + direction,
                 command=lambda: sort_column(col, not reverse))

def get_file_names():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT DISTINCT FileName FROM stocks", conn)
    conn.close()
    return ["All"] + sorted(df["FileName"].dropna().unique().tolist())

# --- Settings Persistence ---
def load_settings():
    """Load saved settings (column widths, window size, filters, github_token) from JSON file"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return {}

def save_settings():
    """Save current settings (column widths, window size, filters, GitHub token) to JSON file"""
    try:
        settings = {
            "window_geometry": root.geometry(),
            "column_widths": {col: tree.column(col, "width") for col in cols if col},
            "file_filter": file_filter.get(),
            "search_col": search_col.get(),
            "search_text": search_text.get(),
            "date_filter": date_filter.get(),
            "last_min": last_min.get(),
            "volume_min": volume_min.get(),
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        print("Settings saved successfully")
    except Exception as e:
        print(f"Error saving settings: {e}")

def apply_saved_settings(settings):
    """Apply previously saved settings to the app"""
    if not settings:
        return
    
    # Restore window geometry
    if "window_geometry" in settings:
        try:
            root.geometry(settings["window_geometry"])
        except Exception as e:
            print(f"Could not restore window geometry: {e}")
    
    # Restore filter values
    if "file_filter" in settings:
        file_filter.set(settings["file_filter"])
    if "search_col" in settings:
        search_col.set(settings["search_col"])
    if "search_text" in settings:
        search_text.set(settings["search_text"])
    if "date_filter" in settings:
        date_filter.set(settings["date_filter"])
    if "last_min" in settings:
        last_min.set(settings["last_min"])
    if "volume_min" in settings:
        volume_min.set(settings["volume_min"])

# GitHub token UI removed — token should be provided via the GITHUB_TOKEN environment variable.


def apply_column_widths(settings):
    """Apply saved column widths to the treeview"""
    if "column_widths" not in settings:
        return
    
    col_widths = settings["column_widths"]
    for col in cols:
        if col in col_widths:
            try:
                tree.column(col, width=col_widths[col])
            except Exception as e:
                print(f"Could not restore width for column {col}: {e}")


# Initialize database on startup
init_db()

# Load saved settings before creating UI
saved_settings = load_settings()

root = tb.Window(themename="superhero")
root.title("Stock Scanner")
root.geometry("1150x650")

# Set window close handler to save settings
def on_closing():
    save_settings()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

style = ttk.Style()
style.configure("Treeview.Heading", padding=(5, 2))

# --- Top Section Layout ---
frame_top = ttk.Frame(root)
frame_top.pack(fill="x", pady=10, padx=10)

# First row: Buttons
frame_buttons = ttk.Frame(frame_top)
frame_buttons.pack(fill="x", pady=5)

fetch_btn = ttk.Button(frame_buttons, text="🔄 Update Data", command=fetch_data)
fetch_btn.pack(side="left", padx=5)

export_btn = ttk.Button(frame_buttons, text="💾 Export to Excel", command=export_excel)
export_btn.pack(side="left", padx=5)

add_btn = ttk.Button(frame_buttons, text="➕ Add", command=add_row)
add_btn.pack(side="right", padx=5)

delete_btn = ttk.Button(frame_buttons, text="🗑️ Delete", command=delete_selected_rows)
delete_btn.pack(side="right", padx=5)

# Add loading indicator (hidden by default)
progress_label = ttk.Label(frame_buttons, text="⏳ Fetching data, please wait...", font=("Segoe UI", 12, "italic"))

# Second row: Filters
filter_container = ttk.LabelFrame(frame_top, text="Filters")
filter_container.pack(fill="x", padx=10, pady=5)

frame_filters = ttk.Frame(frame_top)
frame_filters.pack(fill="x", pady=5)

# variables (KEEP THIS)
file_filter = tk.StringVar(value="All")
search_col = tk.StringVar(value="All")
search_text = tk.StringVar()
date_filter = tk.StringVar(value="All")
last_min = tk.DoubleVar(value=10.00)
volume_min = tk.DoubleVar(value=1_000_000)

# dropdowns (IMPORTANT: you must recreate them BEFORE using .grid)
file_dropdown = ttk.Combobox(
    frame_filters,
    textvariable=file_filter,
    values=get_file_names(),
    width=20
)
col_dropdown = ttk.Combobox(frame_filters, textvariable=search_col,
                            values=["All", "Symbol", "Name", "Exchange", "Sector", "Industry"])
date_dropdown = ttk.Combobox(frame_filters, textvariable=date_filter, values=["All"])

# Configure grid columns to expand
for i in range(12):
    frame_filters.columnconfigure(i, weight=1)

# Row 0
ttk.Label(frame_filters, text="File").grid(row=0, column=0, padx=5, sticky="w")
file_dropdown.grid(row=0, column=1, padx=5, sticky="ew")

ttk.Label(frame_filters, text="Column").grid(row=0, column=2, padx=5, sticky="w")
col_dropdown.grid(row=0, column=3, padx=5, sticky="ew")

ttk.Entry(frame_filters, textvariable=search_text).grid(row=0, column=4, padx=5, sticky="ew")

ttk.Label(frame_filters, text="Date").grid(row=0, column=5, padx=5, sticky="w")
date_dropdown.grid(row=0, column=6, padx=5, sticky="ew")

# Row 1 (move less important filters down)
ttk.Label(frame_filters, text="Last >").grid(row=1, column=0, padx=5, sticky="w")
ttk.Entry(frame_filters, textvariable=last_min).grid(row=1, column=1, padx=5, sticky="ew")

ttk.Label(frame_filters, text="Volume >").grid(row=1, column=2, padx=5, sticky="w")
ttk.Entry(frame_filters, textvariable=volume_min).grid(row=1, column=3, padx=5, sticky="ew")

ttk.Button(frame_filters, text="🔍 Apply Filter", command=apply_filter)\
    .grid(row=1, column=4, padx=10, sticky="ew")


# --- Table Frame (to hold tree + scrollbars) ---
total_label = ttk.Label(root, text="Total records: 0", font=("Segoe UI", 10, "bold"))
total_label.pack(padx=10,  anchor="w")

table_frame = ttk.Frame(root)
table_frame.pack(fill="both", expand=True, padx=10, pady=10)

# --- Scrollbars ---
scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")

# --- Table ---
cols = ["FileName", "Symbol", "Name", "Exchange", "Sector", "Industry", "Last", "Volume", "SCTR", "U", "Date"]

tree = ttk.Treeview(
    table_frame,
    columns=cols,
    show="headings",
    yscrollcommand=scroll_y.set,
    xscrollcommand=scroll_x.set
)

tree["show"] = "headings"
tree.configure(displaycolumns=cols)

# Configure scrollbars
scroll_y.config(command=tree.yview)
scroll_x.config(command=tree.xview)

# Pack scrollbars
scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")

# Pack treeview
tree.pack(fill="both", expand=True)

# Configure columns
for col in cols:
    tree.heading(
        col,
        text=col,
        anchor="w",
        command=lambda c=col: sort_column(c, False)
    )
    tree.column(col, width=150, anchor="w", stretch=False) 

# --- Restore saved filter values and window geometry ---
apply_saved_settings(saved_settings)

# --- Load Data Initially ---
load_data()

root.mainloop()
