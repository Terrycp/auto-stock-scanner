# app_github - Complete Architecture & Logic Documentation

**Project**: Stock Scanner with GitHub Integration  
**Location**: `d:\Project\Python\backup\app_github\`  
**Created**: For automated stock scanning with GUI and GitHub data sync  
**Language**: Python 3

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [Configuration](#configuration)
7. [GUI Features](#gui-features)
8. [Filtering & Sorting Logic](#filtering--sorting-logic)
9. [GitHub Integration](#github-integration)
10. [Code Modules](#code-modules)
11. [Usage Examples](#usage-examples)
12. [API Reference](#api-reference)

---

## Workflow at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE COMPLETE WORKFLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  AUTOMATED (Runs Weekdays via GitHub Actions)                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ fetch_data.py → Scrapes StockCharts → Updates GitHub DB │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  MANUAL (User clicks button in app)                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Download GitHub DB → Merge with local DB → UI updates  │  │
│  │                                                         │  │
│  │ 🔑 Key: Uses composite key (FileName + Symbol + Date)  │  │
│  │         Only NEW records inserted (duplicates filtered) │  │
│  │         User manual add/delete preserved               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  USER INTERACTION (View, filter, export)                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Filter by scan, date, price, volume → Sort → Export    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Overview

### Purpose
The Stock Scanner automates the collection of stock data from StockCharts.com technical analysis scans via GitHub Actions, and provides a rich GUI for viewing, filtering, sorting, and exporting this data. Users can sync with the latest GitHub data with a single click.

### Key Features
- ✅ **Automated Data Fetching**: GitHub Actions scrapes 17 technical analysis scans from StockCharts (Mon-Fri on schedule)
- ✅ **One-Click Sync**: Download latest data from GitHub with "Fetch & Update Data" button
- ✅ **Merge Not Replace**: New data merges into local DB, preserving user manual changes
- ✅ **GUI Interface**: Desktop application with filtering, sorting, and exporting capabilities
- ✅ **Persistent Storage**: SQLite database with dynamic schema
- ✅ **Settings Persistence**: Saves window geometry, column widths, filter values
- ✅ **Data Management**: Add/edit/delete rows manually through GUI (all preserved on sync)
- ✅ **Export Functionality**: Export filtered data to Excel with formatting
- ✅ **Headless Support**: `fetch_data.py` for GitHub Actions automation

### Tech Stack
- **UI**: Tkinter + ttkbootstrap (modern themes)
- **Web Scraping**: BeautifulSoup + requests
- **Data Processing**: Pandas
- **Database**: SQLite3
- **API Integration**: GitHub REST API

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                              │
│                                                              │
│  StockCharts.com (17 technical analysis scans)              │
│  └─ Bullish Catapult, Bear Trap, MACD Crossover, etc.      │
└─────────────────────────┬──────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   app_github │  │  fetch_data  │  │  GitHub API  │
│   (GUI App)  │  │  (Headless)  │  │  (Download)  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  sqlite3 DB     │
                │ stock_data.db   │
                └─────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    ┌────────┐      ┌────────┐      ┌────────┐
    │ Viewing│      │Filtering│     │Export  │
    │(GUI)   │      │(GUI)    │     │(Excel) │
    └────────┘      └────────┘      └────────┘
```

---

## Core Components

### 1. Main Application: `app_github.py`

**File Size**: ~1,200 lines  
**Purpose**: GUI application for viewing, filtering, and managing stock data

**Main Functions**:

| Function | Purpose |
|----------|---------|
| `init_db()` | Initialize SQLite database with stocks table |
| `download_latest_data()` | Download latest GitHub DB and merge only new records |
| `fetch_data()` | Alias for `download_latest_data()` in the GUI app |
| `load_data()` | Load all records from database into GUI |
| `refresh_table(df)` | Update table display with DataFrame |
| `apply_filter()` | Apply user-selected filters to data |
| `export_excel()` | Export filtered data to Excel file |
| `add_row()` | Open dialog to manually add a stock record |
| `delete_selected_rows()` | Delete selected rows from database and record deletions |
| `sort_column(col, reverse)` | Sort table by clicked column header |
| `save_settings()` / `load_settings()` | Persist user preferences to JSON |

**Dependencies**:
- tkinter, ttkbootstrap (GUI)
- pandas (data manipulation)
- sqlite3 (database)
- requests, BeautifulSoup (web scraping)
- datetime (date parsing)

### 2. Headless Fetcher: `fetch_data.py`

**File Size**: ~180 lines  
**Purpose**: Standalone data fetcher for automation/CI-CD (no GUI)

**Main Function**:
- `fetch_data()` - Single function that fetches and inserts data into database

**Use Cases**:
- GitHub Actions scheduled runs
- Command-line automated execution
- Server-side batch processing
- Webhook-triggered updates

**No Dependencies on GUI** - Pure data fetching logic

---

## Data Flow

### Flow 1: User Opens App (GUI)

```
1. app_github.py starts
   ├─ init_db()             → Create/verify database
   ├─ load_settings()       → Restore saved preferences
   ├─ UI initialized
   └─ load_data()           → Populate table with all records
   
2. User clicks "🔄 Fetch & Update Data"
   ├─ start_loading()       → Disable buttons, show spinner
   ├─ download_latest_data()
   │  ├─ Download latest DB from GitHub
   │  ├─ Load GitHub DB into temporary file
   │  ├─ Compare with local DB
   │  ├─ Filter new symbols only (composite key: FileName + Symbol + Date)
   │  ├─ Insert only NEW records into local DB
   │  └─ Preserve all user manual add/delete changes
   ├─ file_dropdown updated → Refresh scan names
   ├─ load_data()           → Refresh table
   └─ stop_loading()        → Re-enable buttons
   
3. User applies filters (File, Date, Price, Volume, Text)
   ├─ apply_filter()        → Build SQL WHERE clause
   ├─ Query database
   ├─ refresh_table(df)     → Update display
   └─ Format numbers for display
   
4. User exports to Excel
   ├─ export_excel()        → Format data
   ├─ filedialog.asksaveasfilename()
   ├─ df.to_excel(path)
   └─ messagebox confirmation
   
5. User closes app
   └─ on_closing()
      ├─ save_settings()    → Persist preferences
      └─ root.destroy()     → Close window
```

### Flow 2: Automated GitHub Actions (Runs Weekdays on Schedule)

```
GitHub Actions (scheduled trigger - e.g., Mon-Fri at 9 AM)
   │
   ▼
python fetch_data.py
   │
   ├─ fetch_data()
   │  ├─ init_db()         → Create DB if needed
   │  ├─ Loop through 17 URLs (StockCharts.com)
   │  ├─ Parse HTML tables
   │  ├─ Filter new symbols only
   │  └─ Insert new records into GitHub DB
   │
   ├─ Git commit: "Update stock data"
   └─ Push updated stock_data.db to repository
```

### Flow 3: User Syncs with Latest Data (GitHub → Local)

```
User clicks "🔄 Fetch & Update Data" button
   │
   ├─ download_latest_data()
   │  │
   │  ├─ Download latest DB from GitHub (via API)
   │  ├─ Save to temporary file
   │  ├─ Open both local and GitHub databases
   │  │
   │  ├─ Create composite key from:
   │  │  ├─ FileName (scan name)
   │  │  ├─ Symbol (stock ticker)
   │  │  └─ Date (scan date)
   │  │
   │  ├─ Find records in GitHub DB not in local DB
   │  ├─ Insert only NEW records
   │  ├─ ✅ Preserve all user manual changes
   │  └─ Clean up temporary file
   │
   └─ Result: Local DB has latest data + user changes
```

---

## Database Schema

### SQLite Table: `stocks`

```sql
CREATE TABLE IF NOT EXISTS stocks (
    FileName TEXT,           -- Name of the scan (e.g., "Bullish Engulfing")
    Symbol TEXT,             -- Stock ticker (e.g., "AAPL")
    Name TEXT,               -- Company name (e.g., "Apple Inc")
    Exchange TEXT,           -- Stock exchange (NYSE, NASDAQ, etc.)
    Sector TEXT,             -- Industry sector (Technology, Healthcare, etc.)
    Industry TEXT,           -- Specific industry classification
    Last REAL,               -- Current stock price
    Volume INTEGER,          -- Trading volume
    SCTR REAL,               -- StockCharts Technical Rank (0-100)
    U TEXT,                  -- Unknown column (part of StockCharts data)
    Date TEXT                -- Date scan was run (YYYY-MM-DD format)
);
```

### Dynamic Columns

Additional columns can be added automatically:
- If a scan returns columns not in the schema, they're added as TEXT columns
- Handled by `add_missing_columns_dynamic(df, "stocks")`

### Example Data

```
FileName                    | Symbol | Name              | Last  | Volume    | SCTR | Date
──────────────────────────────────────────────────────────────────────────────────────────
Bullish Engulfing          | AAPL   | Apple Inc         | 127.5 | 52300000  | 88   | 2026-05-10
Bullish Engulfing          | MSFT   | Microsoft Corp    | 420.1 | 21400000  | 85   | 2026-05-10
Bear Trap                  | TSLA   | Tesla Inc         | 245.3 | 118500000 | 72   | 2026-05-10
Bullish MACD Crossover     | NVDA   | NVIDIA Corp       | 890.2 | 38200000  | 92   | 2026-05-10
```

### Key Characteristics

- **No Primary Key**: Allows duplicate entries if needed (same stock in different scans)
- **Dynamic Schema**: New columns added as encountered
- **Text-heavy**: Most values stored as TEXT for flexibility
- **Date Field**: All records tagged with scan date (YYYY-MM-DD)

---

## Configuration

### Global Configuration in `app_github.py`

```python
# Database location (same directory as script)
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_data.db")

# Settings file (persists user preferences)
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_settings.json")

# GitHub authentication
GITHUB_TOKEN = "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"

# 17 Stock Scans (from StockCharts.com)
URL_LIST = [
    ("Bullish Catapult", "https://stockcharts.com/def/servlet/SC.scan?..."),
    ("Bear Trap", "https://stockcharts.com/def/servlet/SC.scan?..."),
    # ... 15 more scans
]

# HTTP headers (appears as regular browser)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Standard columns that all scans should have
STANDARD_COLS = [
    "Symbol", "Name", "Exchange", "Sector", "Industry",
    "Last", "Volume", "SCTR", "U",
    "Daily MACD Line(12,26,9,Daily Close)",
    "Daily RSI(14,Daily Close)"
]
```

### Settings File: `app_settings.json`

```json
{
    "window_geometry": "1150x650+201+105",
    "column_widths": {
        "FileName": 150,
        "Symbol": 150,
        "Name": 150,
        "Exchange": 150,
        "Sector": 150,
        "Industry": 150,
        "Last": 150,
        "Volume": 150,
        "SCTR": 150,
        "U": 150,
        "Daily MACD Line(12,26,9,Daily Close)": 150,
        "Daily RSI(14,Daily Close)": 150,
        "Date": 150
    },
    "file_filter": "All",
    "search_col": "All",
    "search_text": "",
    "date_filter": "All",
    "last_min": 10.0,
    "volume_min": 1000000.0
}
```

**Persisted Settings**:
- Window size and position
- Column widths for each column
- All filter values (scan, search column, search text, date, price/volume minimums)
- Auto-restored on app startup

---

## GUI Features

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  📈 Stock Scanner UI                                    │
├─────────────────────────────────────────────────────────┤
│  [🔄 Fetch]  [💾 Export]  [➕ Add] [🗑️ Delete]          │
│  [⏳ Fetching...]                                        │
├─────────────────────────────────────────────────────────┤
│ Filters                                                 │
│  File: [Bullish Engulfing ▼]  Col: [Symbol ▼]         │
│  Search: [search text...]      Date: [2026-05-10 ▼]   │
│  Last > [10.00]  Volume > [1000000]  [🔍 Apply Filter]│
├─────────────────────────────────────────────────────────┤
│ Total records: 523                                      │
├─────────────────────────────────────────────────────────┤
│ FileName     │ Symbol │ Name        │ Last  │ Volume   │
│──────────────┼────────┼─────────────┼───────┼──────────┤
│ Bull Engulf. │ AAPL   │ Apple Inc   │127.50 │52,300K   │
│ Bull Engulf. │ MSFT   │ Microsoft   │420.10 │21,400K   │
│ Bear Trap    │ TSLA   │ Tesla       │245.30 │118,500K  │
│ ...          │ ...    │ ...         │ ...   │ ...      │
└─────────────────────────────────────────────────────────┘
```

### Components

#### Top Section: Buttons

| Button | Action | Function |
|--------|--------|----------|
| 🔄 Fetch & Update Data | Scrape all 17 URLs | `fetch_data()` |
| 💾 Export to Excel | Save filtered data | `export_excel()` |
| ➕ Add | Open dialog to add row | `add_row()` |
| 🗑️ Delete | Delete selected rows | `delete_selected_rows()` |

#### Filters Section

| Filter | Type | Default | Purpose |
|--------|------|---------|---------|
| File | Dropdown | "All" | Filter by scan name (FileName) |
| Column | Dropdown | "All" | Which column to search in |
| Search | Text box | "" | Text to search for (case-insensitive) |
| Date | Dropdown | "All" | Filter by scan date |
| Last > | Number | 10.0 | Minimum stock price filter |
| Volume > | Number | 1000000 | Minimum trading volume filter |

#### Table Display

- **Dynamic columns** based on database schema
- **Sortable columns** - click header to sort ascending/descending
- **Sort indicators** - 🔼 for ascending, 🔽 for descending
- **Number formatting**:
  - Volume: `52,300,000` (comma-separated)
  - Price/SCTR: `127.50` (2 decimal places)
  - MACD/RSI: `2.50` (2 decimal places)
- **Scrollbars** - both vertical and horizontal
- **Status line** - "Total records: X" showing row count

---

## Filtering & Sorting Logic

### Filter Application (`apply_filter()`)

```python
def apply_filter(*args):
    # Build SQL query dynamically
    query = "SELECT * FROM stocks WHERE 1=1"
    params = []

    # 1. File filter (FileName)
    if file_filter.get() != "All":
        query += " AND FileName = ?"
        params.append(file_filter.get())
    
    # 2. Text search in specific column
    if search_col.get() != "All" and search_text.get():
        query += f" AND {search_col.get()} LIKE ?"
        params.append(f"%{search_text.get()}%")
    
    # 3. Date filter
    if date_filter.get() != "All":
        query += " AND Date = ?"
        params.append(date_filter.get())

    # 4. Price filter (Last > minimum)
    query += " AND Last > ?"
    params.append(last_min.get())
    
    # 5. Volume filter (Volume > minimum)
    query += " AND Volume > ?"
    params.append(volume_min.get())

    # Execute query and refresh display
    df = pd.read_sql(query, conn, params=params)
    refresh_table(df)
```

**Filter Logic**:
- All filters use **AND logic** - must pass ALL conditions
- Filters are **optional** - can be left at "All" to disable
- Numeric filters use **> comparison** (greater than)
- Text search is **case-insensitive** with **LIKE wildcard**

### Sorting (`sort_column()`)

```python
def sort_column(col, reverse):
    # Convert column to numeric if possible
    sorted_df = current_df.copy()
    sorted_df[col] = pd.to_numeric(sorted_df[col], errors='ignore')
    
    # Sort by column (ascending/descending based on reverse flag)
    sorted_df = sorted_df.sort_values(by=col, ascending=not reverse)
    
    # Update display with sort indicator (🔼 or 🔽)
    refresh_table(sorted_df)
    
    # Add arrow to sorted column header
    direction = " 🔽" if reverse else " 🔼"
    tree.heading(col, text=col + direction,
                 command=lambda: sort_column(col, not reverse))
```

**Sorting Features**:
- **Click column header** to sort
- **Click again** to reverse sort order
- **Numeric columns** sorted numerically (not as strings)
- **String columns** sorted alphabetically
- **Visual indicator** (🔼/🔽) shows sort direction

### Example Filter Chains

**Example 1**: Show all Bullish Engulfing stocks over $50
```python
file_filter = "Bullish Engulfing"
last_min = 50.0
volume_min = 1_000_000
date_filter = "All"
search_col = "All"
```
Result: Only Bullish Engulfing stocks with price > $50 and volume > 1M

**Example 2**: Find all "TECH" companies from today
```python
file_filter = "All"
search_col = "Name"
search_text = "TECH"
date_filter = "2026-05-10"
last_min = 10.0
volume_min = 1_000_000
```
Result: Companies with "TECH" in name from specified date

**Example 3**: Show expensive low-volume stocks
```python
last_min = 100.0  # Price over $100
volume_min = 0.0  # Remove volume filter
```
Result: All stocks over $100 (volume doesn't matter)

---

## GitHub Integration

### GitHub API Configuration

```python
GITHUB_OWNER = "Terrycp"              # GitHub username
GITHUB_REPO = "auto-stock-scanner"    # Repository name
GITHUB_BRANCH = "main"                # Default branch
GITHUB_TOKEN = "github_pat_..."       # Personal access token
```

### Database Merge (`download_latest_data()`) - Button Function

**When**: User clicks "🔄 Fetch & Update Data" button

**What it does**:
1. Downloads latest `stock_data.db` from GitHub
2. Saves to temporary file for comparison
3. Opens connections to both local and GitHub databases
4. Reads all records from GitHub database
5. Creates composite key: `(FileName, Symbol, Date)`
6. Compares with local database to find NEW records
7. Inserts only NEW records (preserves user manual changes)
8. Cleans up temporary file
9. Refreshes UI with merged data

**Key Feature**: **Filters new symbols only** - uses composite key to prevent duplicates

**Code**:
```python
def download_latest_data():
    try:
        # Download latest DB from GitHub
        response = requests.get(api_url, headers=headers_req, timeout=15)
        response.raise_for_status()
        
        # Save to temporary file
        temp_db_path = f"{DB_NAME}.temp"
        with open(temp_db_path, 'wb') as f:
            f.write(response.content)
        
        # Open both databases
        local_conn = sqlite3.connect(DB_NAME)
        github_conn = sqlite3.connect(temp_db_path)
        
        # Read GitHub data
        github_df = pd.read_sql("SELECT * FROM stocks", github_conn)
        github_conn.close()
        
        # Get local composite keys
        local_df = pd.read_sql("SELECT FileName, Symbol, Date FROM stocks", local_conn)
        local_keys = set(zip(local_df["FileName"], local_df["Symbol"], local_df["Date"]))
        
        # Filter to new records only
        new_records = github_df[
            github_df.apply(
                lambda row: (row["FileName"], row["Symbol"], row["Date"]) not in local_keys,
                axis=1
            )
        ]
        
        # Insert new records
        if len(new_records) > 0:
            add_missing_columns_dynamic(new_records, "stocks")
            new_records.to_sql("stocks", local_conn, if_exists="append", index=False)
            print(f"✅ Inserted {len(new_records)} new records")
        
        local_conn.close()
        os.remove(temp_db_path)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        messagebox.showerror("Error", f"Failed to download from GitHub: {e}")
```

### Data Preservation Strategy

- ✅ **Merges instead of replaces** - local DB never overwritten
- ✅ **Preserves user changes** - manual add/delete records kept
- ✅ **Uses composite key** - prevents duplicate entries
- ✅ **Conflict-free** - GitHub data extends local DB, doesn't override

### GitHub Actions Workflow (Automated Weekday Scraping)

Configured in `.github/workflows/scan.yml`:

```yaml
name: Stock Scan
on:
  schedule:
    - cron: '0 9 * * 1-5'  # Mon-Fri at 9 AM UTC

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python fetch_data.py
      - run: git add stock_data.db
      - run: git commit -m "Auto-update: stock data $(date +%Y-%m-%d)"
      - run: git push
```

**What happens**:
1. GitHub Actions runs `fetch_data.py` on weekday schedule
2. Scrapes all 17 StockCharts scans
3. Filters new symbols only
4. Updates `stock_data.db` in repository
5. Commits and pushes changes
6. Users can now sync by clicking button anytime

**Benefits**:
- ✅ Automated data collection (no manual intervention)
- ✅ Always fresh data available in GitHub
- ✅ Users get latest data with single click
- ✅ Works even if user's internet is slow/unreliable

---

## Code Modules

### Module 1: `app_github.py` (Main Application)

**Purpose**: Complete GUI stock scanner application

**Key Sections**:

#### Initialization
```python
# Global state
current_df = pd.DataFrame()
is_loading = False

# Configuration (URLs, columns, tokens)
DB_NAME, SETTINGS_FILE, GITHUB_TOKEN
URL_LIST (17 scans)
HEADERS, STANDARD_COLS

# Database functions
init_db()
add_column_if_not_exists()
add_missing_columns_dynamic()
```

#### Core Operations
```python
# Fetching
fetch_data()          # Scrape and insert

# UI Updates
load_data()           # Load all from DB
refresh_table(df)     # Update display
start_loading()       # Show loading spinner
stop_loading()        # Hide spinner

# Filtering & Sorting
apply_filter()        # Apply user filters
sort_column()         # Sort by column
update_date_filter()  # Update date dropdown
```

#### Data Management
```python
add_row()             # Dialog to add stock
delete_selected_rows()# Delete from DB
export_excel()        # Export filtered data
```

#### Settings Persistence
```python
load_settings()       # Load from JSON
save_settings()       # Save to JSON
apply_saved_settings()# Restore on startup
apply_column_widths() # Restore column sizes
```

#### GitHub Integration
```python
download_latest_data()  # Download from GitHub and merge new symbols
fetch_data()            # Alias for download_latest_data()
```

#### UI Setup
```python
# GUI components creation
tkinter buttons, dropdowns, text entries
treeview for table display
scrollbars and layout

# Event binding
file_filter.trace() -> apply_filter()
search_text.trace() -> apply_filter()
root.protocol("WM_DELETE_WINDOW", on_closing)
```

### Module 2: `fetch_data.py` (Headless Fetcher)

**Purpose**: Standalone data fetcher for automation

**Key Function**:
```python
def fetch_data():
    """Fetch stock data from URLs and update database"""
    
    # Initialize database
    init_db()
    conn = sqlite3.connect(DB_NAME)
    
    # Loop through each scan URL
    for scan_name, link in URL_LIST:
        time.sleep(1)  # Rate limiting
        
        try:
            # 1. Fetch HTML
            resp = requests.get(link, headers=HEADERS)
            resp.raise_for_status()
            
            # 2. Parse with BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # 3. Extract metadata
            file_name = soup.find(class_="scan-name").get_text(strip=True)
            date_tag = soup.find(id="table-date")
            formatted_date = parse_date_from_html(date_tag)
            
            # 4. Extract table
            table = soup.find("table", {"id": "sccDataTable"})
            df_new = pd.read_html(StringIO(str(table)))[0]
            
            # 5. Normalize columns
            normalize_dataframe(df_new)
            df_new["FileName"] = file_name
            df_new["Date"] = formatted_date
            
            # 6. Get existing symbols for this scan
            old_symbols = get_existing_symbols(conn, file_name, formatted_date)
            
            # 7. Insert only new records
            new_symbols = df_new[~df_new["Symbol"].isin(old_symbols)]
            if len(new_symbols) > 0:
                add_missing_columns_dynamic(new_symbols, "stocks")
                new_symbols.to_sql("stocks", conn, if_exists="append", index=False)
                print(f"Inserted {len(new_symbols)} new records for {file_name}")
            
        except Exception as e:
            print(f"Error fetching {scan_name}: {e}")
    
    conn.close()
    print("✅ Fetch & Update complete!")
```

**Features**:
- No GUI dependencies
- Clean, readable logic
- Comprehensive error handling
- Console logging for debugging

---

## Usage Examples

### Example 1: Basic App Launch

```python
# Run the application
python app_github.py

# What happens:
# 1. Initializes local database (creates if missing)
# 2. Loads saved settings (window size, filters)
# 3. Displays GUI
# 4. Loads all stock records from local database into table
# 5. Ready for user interaction
# 
# Note: To get latest data, click "🔄 Fetch & Update Data" button
```

### Example 2: Sync Latest Data from GitHub

```
User clicks: "🔄 Fetch & Update Data"

# Backend:
1. Downloads latest stock_data.db from GitHub repository
2. Opens temporary file (GitHub DB) and local database
3. Reads all records from GitHub DB
4. Creates composite key: (FileName, Symbol, Date)
5. Finds records NOT in local database
6. For each new record:
   - Ensures all columns exist (dynamic schema)
   - Inserts into local database
7. Cleans up temporary file
8. Updates file dropdown (scan names)
9. Refreshes table display
10. Shows message: "✅ Inserted X new records"

# Result:
Local database updated with latest GitHub data
All user manual add/delete records preserved

# Note:
GitHub data is updated automatically by GitHub Actions (weekdays)
User just needs to click button to get latest available data
```

### Example 3: Filter for Bullish Signals

**Scenario**: Find all "Bullish Engulfing" stocks over $50 with volume > 2M from today

**Steps**:
1. Click File dropdown → Select "Bullish Engulfing"
2. Change "Last >" to `50`
3. Change "Volume >" to `2000000`
4. Click Date dropdown → Select today's date
5. Click "🔍 Apply Filter"

**SQL Generated**:
```sql
SELECT * FROM stocks 
WHERE FileName = 'Bullish Engulfing'
  AND Date = '2026-05-10'
  AND Last > 50.0
  AND Volume > 2000000
```

**Result**: Table shows only matching stocks, formatted:
- Prices: `127.50` (2 decimals)
- Volumes: `52,300,000` (comma-separated)

### Example 4: Search for Specific Company

**Scenario**: Find all Tesla (TSLA) entries across all scans

**Steps**:
1. Leave File = "All"
2. Change Column to "Symbol"
3. Type "TSLA" in search box
4. Click "🔍 Apply Filter"

**Result**: Shows all TSLA records from all 17 scans, all dates

### Example 5: Add Manual Entry

**Scenario**: Add a stock that wasn't in the scans

**Steps**:
1. Click "➕ Add" button
2. Dialog appears with fields:
   - FileName: "Manual Entry" (default)
   - Symbol: "ABC"
   - Name: "ABC Company"
   - Exchange: "NASDAQ"
   - Sector: "Technology"
   - Industry: "Software"
   - Last: "123.45"
   - Volume: "1000000"
   - SCTR: "85"
   - Date: Today (auto-filled)
3. Click "Save"

**Result**: New record added to database and appears in table

### Example 6: Export Filtered Data

**Scenario**: Export all "Bear Trap" stocks to Excel

**Steps**:
1. Filter File = "Bear Trap"
2. Click "💾 Export to Excel"
3. File dialog appears
4. Choose location: `C:\Users\YourName\Desktop\bear_traps.xlsx`
5. Click Save

**Result**: Excel file created with:
- All columns from database
- Formatted numbers (prices with 2 decimals, volumes with commas)
- Filtered rows only
- Date preserved

### Example 7: Automated Headless Execution

```bash
# Run fetch_data.py from command line
python fetch_data.py

# Output:
# Fetching scan 1: Bullish Catapult
# Fetching scan 2: Quadruple Top Breakout
# ... (15 more)
# Inserted 45 new records for Bullish Catapult
# Inserted 32 new records for Bear Trap
# No new records for Bullish Triangle
# ✅ Fetch & Update complete!

# Database updated with new stocks
# Can be committed to GitHub automatically
```

### Example 8: Sort by Multiple Criteria

**Scenario**: Find highest SCTR stocks from most expensive to least

**Steps**:
1. Click "SCTR" column header → Sorts ascending (🔼)
2. Click "SCTR" again → Sorts descending (🔽) - highest first
3. Click "Last" column header → Now sorted by price (highest first)

**Result**: Can quickly identify trends

### Example 9: Delete Outdated Records

**Scenario**: Remove all data from 5 days ago

**Steps**:
1. Filter Date = "2026-05-05"
2. Ctrl+A or click header checkbox (if available)
3. Click "🗑️ Delete"
4. Confirm: "Delete selected rows from the database?"
5. Confirm deletion

**Result**: All records from that date removed

### Example 10: Check Today's Hot Stocks

**Scenario**: Quick overview of today's scanning results

**Steps**:
1. App opens (auto-loads latest data)
2. Check Date filter = "2026-05-10"
3. Look at Total records count
4. Sort by SCTR (highest first) - best technical performers
5. View by File dropdown - which scans had most hits
6. Export to share with team

**Result**: Quick snapshot of market scanning results

---

## API Reference

### Database Functions

#### `init_db()`
```python
def init_db():
    """Initialize SQLite database with stocks table"""
    # Creates stocks table if not exists
    # Columns: FileName, Symbol, Name, Exchange, Sector, Industry, 
    #          Last, Volume, SCTR, U, Date
```

#### `add_missing_columns_dynamic(df, table_name)`
```python
def add_missing_columns_dynamic(df, table_name):
    """Add any new columns from DataFrame to database table"""
    # Compares df columns with existing table schema
    # Creates new columns (as TEXT) for any missing ones
    # Handles dynamic data from different scans
```

#### `add_column_if_not_exists(db_name, table_name, column_name, column_type)`
```python
def add_column_if_not_exists(db_name, table_name, column_name, column_type):
    """Add single column if not already exists"""
    # Used for specific columns (less common now)
```

### Scraping Functions

#### `fetch_data()` (in `app_github.py`)
```python
def fetch_data():
    """
    GUI button callback that downloads and merges the latest GitHub DB.
    - Calls `download_latest_data()`
    - Runs inside the UI loading state
    - Refreshes the table once merge completes
    """
```

#### `fetch_data()` (in `fetch_data.py`)
```python
def fetch_data():
    """
    Standalone scraping function (no GUI dependencies).
    - Fetches all 17 StockCharts URLs
    - Parses HTML tables and standardizes columns
    - Inserts only new records into the local DB
    - Suitable for automation/CI-CD
    """
```

### UI Functions

#### `load_data()`
```python
def load_data():
    """Load all stock records from database into GUI table"""
    # Fetches all records
    # Sets column headers
    # Applies saved column widths
    # Refreshes display
    # Updates date filter dropdown
```

#### `refresh_table(df)`
```python
def refresh_table(df):
    """Update table display with DataFrame contents"""
    # Clears existing rows
    # Formats numeric columns (prices, volumes, SCTR, RSI, MACD)
    # Inserts new rows
    # Updates total record count
```

#### `apply_filter(*args)`
```python
def apply_filter(*args):
    """Apply user-selected filters and update display"""
    # Builds SQL WHERE clause from filter values
    # Executes query
    # Updates table
    # Filters:
    #   - FileName (scan type)
    #   - Text search in column
    #   - Date
    #   - Last (price) > minimum
    #   - Volume > minimum
    # All filters are optional and use AND logic
```

#### `export_excel()`
```python
def export_excel():
    """Export currently displayed data to Excel file"""
    # Formats numeric columns
    # Asks user for save location
    # Creates Excel file with current filtered data
    # Shows confirmation message
```

#### `add_row()`
```python
def add_row():
    """Open dialog to manually add stock record to database"""
    # Creates Toplevel window with input fields
    # Fields: FileName, Symbol, Name, Exchange, Sector, Industry,
    #         Last, Volume, SCTR, U, Date
    # Validation: Symbol required
    # Auto-fills: FileName="Manual Entry", Date=today
    # Saves to database
    # Refreshes UI
```

#### `delete_selected_rows()`
```python
def delete_selected_rows():
    """Delete selected rows from database"""
    # Gets selected rows from table
    # Asks for confirmation
    # Deletes by FileName + Symbol + Date
    # Refreshes UI
```

#### `sort_column(col, reverse)`
```python
def sort_column(col, reverse):
    """Sort table by column"""
    # Converts column to numeric if possible
    # Sorts ascending/descending based on reverse flag
    # Updates display
    # Shows sort indicator (🔼/🔽)
```

### Settings Functions

#### `load_settings()`
```python
def load_settings():
    """Load saved preferences from app_settings.json"""
    # Returns dict with:
    #   - Window geometry
    #   - Column widths
    #   - Filter values (file, column, text, date, price, volume)
    # Returns empty dict if file not found
```

#### `save_settings()`
```python
def save_settings():
    """Save current app state to app_settings.json"""
    # Saves:
    #   - Current window geometry
    #   - All column widths
    #   - All filter values
    # Called on app close
```

#### `apply_saved_settings(settings)`
```python
def apply_saved_settings(settings):
    """Restore saved settings to app on startup"""
    # Restores window geometry
    # Restores all filter values
    # Restores column widths
```

### GitHub Functions

#### `download_latest_data()`
```python
def download_latest_data():
    """Download latest database from GitHub and merge new records."""
    # Downloads stock_data.db from GitHub using the REST API
    # Saves the remote DB to a temporary file
    # Reads both local and GitHub stocks tables
    # Builds composite keys (FileName, Symbol, Date)
    # Skips rows already present locally
    # Respects manual deletions via deleted_records table
    # Inserts only truly new records into local DB
    # Cleans up temporary file after merging
```

### Utility Functions

#### `get_file_names()`
```python
def get_file_names():
    """Get list of unique scan names from database"""
    # Returns: ["All"] + list of scan names
    # Used to populate file filter dropdown
```

#### `update_date_filter(df)`
```python
def update_date_filter(df):
    """Update date dropdown with available dates"""
    # Extracts unique dates from DataFrame
    # Sorts in reverse (newest first)
    # Updates dropdown values
```

---

## Detailed Architecture Flow

### Data Ingestion Pipeline

```
StockCharts URL
    │
    ▼
HTTP GET (with User-Agent header)
    │
    ▼
Parse HTML with BeautifulSoup
    │
    ├─ Find table (id="sccDataTable")
    ├─ Find scan name (class="scan-name")
    └─ Find date (id="table-date")
    │
    ▼
Convert HTML table to Pandas DataFrame
    │
    ├─ pd.read_html() parses table
    ├─ Remove unnamed index column if exists
    ├─ Strip whitespace from column names
    └─ Ensure all STANDARD_COLS exist (add None if missing)
    │
    ▼
Normalize & Enhance DataFrame
    │
    ├─ Reorder columns to standard order
    ├─ Add FileName (scan name)
    ├─ Add Date (formatted as YYYY-MM-DD)
    └─ Add any extra columns from website
    │
    ▼
Compare with Existing Database
    │
    ├─ Query: SELECT Symbol FROM stocks 
    │          WHERE FileName=? AND Date=?
    ├─ Get list of existing symbols
    └─ Filter DataFrame to NEW symbols only
    │
    ▼
Ensure Database Schema Supports All Columns
    │
    └─ add_missing_columns_dynamic(df, "stocks")
       ├─ Query PRAGMA table_info(stocks)
       ├─ For each new column:
       │  └─ ALTER TABLE stocks ADD COLUMN "colname" TEXT
    │
    ▼
Insert Records into Database
    │
    ├─ df.to_sql("stocks", conn, if_exists="append")
    └─ Print "Inserted N new records for [ScanName]"
```

### Display Rendering Pipeline

```
Database Query
    │
    ├─ If filter applied: WHERE conditions
    └─ If no filter: SELECT * FROM stocks
    │
    ▼
Pandas reads into DataFrame
    │
    ├─ Extract column list
    ├─ Ensure "Date" is last column
    └─ Get unique dates for filter dropdown
    │
    ▼
Format Numeric Values
    │
    ├─ Volume: 1234567 → "1,234,567"
    ├─ Last: 123.4567 → "123.46"
    ├─ SCTR: 88.123 → "88.12"
    ├─ MACD: 1.234 → "1.23"
    └─ RSI: 45.678 → "45.68"
    │
    ▼
Clear Treeview Widget
    │
    ├─ tree.delete(*tree.get_children())
    └─ Remove all existing rows
    │
    ▼
Insert Rows into Treeview
    │
    ├─ For each row in DataFrame:
    │  ├─ Extract values by column
    │  ├─ Format according to column type
    │  └─ tree.insert("", "end", values=[...])
    │
    ▼
Update Status Information
    │
    ├─ total_label.config(text=f"Total records: {len(df)}")
    └─ Show row count in label
    │
    ▼
Display on Screen
```

### Settings Persistence Flow

```
App Startup
    │
    ├─ Check if app_settings.json exists
    ├─ load_settings() → read JSON
    └─ Restore:
       ├─ Window geometry
       ├─ Column widths
       └─ Filter values
    │
    ▼
User Interacts
    │
    └─ Applies filters, sorts, resizes columns
    │
    ▼
App Close (on_closing event)
    │
    ├─ save_settings() → collect current state
    └─ Write to JSON:
       ├─ root.geometry() → window size/position
       ├─ tree.column(col, "width") → each column width
       ├─ All filter values (file, column, text, date, price, volume)
       └─ Save to disk
    │
    ▼
Next App Launch
    │
    └─ load_settings() → Restore everything
```

---

## Security Considerations

### GitHub Token Handling

**Current Implementation**:
- Token stored in source code: `app_github.py` line ~50
- Hard-coded as constant: `GITHUB_TOKEN = "github_pat_..."`

**⚠️ Security Risk**:
- Tokens in source code are dangerous
- Anyone with code access can use token
- Token has full repository access

**Recommended Fix**:
```python
# Use environment variable instead
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Set in GitHub Actions secrets:
# GITHUB_TOKEN: github_pat_...

# Set locally (before running):
# set GITHUB_TOKEN=github_pat_...  (Windows PowerShell)
# export GITHUB_TOKEN=github_pat_...  (Linux/Mac)
```

### Data Privacy

- **Database is local**: All stock data stored on user's machine
- **No cloud sync** (except GitHub which user controls)
- **Settings file** contains filter values only (no sensitive data)

### Web Scraping Ethics

- Respects robots.txt: StockCharts allows scraping
- Includes User-Agent header: Appears as browser
- Uses rate limiting: `time.sleep(1)` between requests
- Read-only access: Never modifies source data

---

## Troubleshooting

### Issue: "Could not download database from GitHub"

**Causes**:
- Invalid token
- Network timeout
- Repository not found
- GitHub API rate limit hit

**Solution**:
1. Check token validity: Go to https://github.com/settings/tokens
2. Verify network connection
3. App will fall back to local database
4. Try again later

### Issue: "No table found for [scan]"

**Cause**: StockCharts website structure changed

**Solution**:
1. Update BeautifulSoup selectors in `fetch_data.py`
2. Manually inspect webpage HTML
3. Update `soup.find()` calls with new selectors

### Issue: Database getting too large

**Symptoms**: Slow performance, large file size

**Solution**:
1. Delete old records: Filter by date, select all, delete
2. Or: Use SQLite VACUUM command
3. Or: Archive old DB and start fresh

### Issue: Columns not displaying correctly

**Cause**: Column widths not restored or window too small

**Solution**:
1. Drag column borders to resize manually
2. Delete `app_settings.json` to reset all settings
3. Maximize window to fit more columns

---

## Summary

The **app_github** project is a comprehensive stock scanner application that:

1. **Automatically fetches** stock data from 17 technical analysis scans
2. **Stores locally** in SQLite with flexible schema
3. **Provides rich GUI** for viewing, filtering, sorting, and exporting
4. **Syncs with GitHub** for collaborative access and automation
5. **Persists settings** for consistent user experience
6. **Supports automation** through headless `fetch_data.py`

The architecture separates concerns:
- **app_github.py**: GUI and user interaction
- **fetch_data.py**: Pure data fetching logic
- **SQLite DB**: Persistent data storage
- **app_settings.json**: User preferences
- **GitHub**: Remote data synchronization

All components work together to provide a seamless stock scanning and analysis tool.
