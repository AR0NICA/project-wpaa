# WPAA Installation and Setup Guide

## Quick Start

### 1. Install Required Packages

```powershell
# Install Python packages
pip install -r requirements.txt
```

### 2. Run Feature Tests

```powershell
python test_wpaa.py
```

### 3. Launch Web Interface

```powershell
python run_web_interface.py
```

Access `http://127.0.0.1:5000` in your browser.

## Detailed Installation Guide

### 1. Check Python Environment

```powershell
python --version
```

Python 3.7 or higher is required.

### 2. Create Virtual Environment (Recommended)

```powershell
# Create virtual environment
python -m venv wpaa_env

# Activate virtual environment
wpaa_env\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3. Install Graphviz

1. Download Windows installer from [Graphviz official website](https://graphviz.org/download/)
2. Add bin directory to system PATH after installation
   - Example: `C:\Program Files\Graphviz\bin`

### 4. Install ChromeDriver (Optional)

Required for dynamic webpage analysis.

1. Download from [ChromeDriver website](https://sites.google.com/chromium.org/driver/)
2. Select version compatible with your Chrome browser
3. Add executable to PATH or save in project directory

## Usage

### Web Interface (Recommended)

```powershell
python run_web_interface.py
```

### Command Line Interface

```powershell
# Basic analysis
python wpaa_run.py --urls https://example.com

# Advanced options
python wpaa_run.py --urls https://example.com --export-html --compare-changes --show-performance
```

## Troubleshooting

### ImportError Issues

```powershell
pip install --upgrade -r requirements.txt
```

### Graphviz Related Errors

1. Verify Graphviz is properly installed
2. Check that Graphviz bin directory is added to PATH environment variable

### ChromeDriver Related Errors

1. Verify Chrome browser is installed
2. Check ChromeDriver and Chrome version compatibility
3. Ensure ChromeDriver is in PATH

## Feature Usage Examples

### 1. Basic Webpage Analysis

```powershell
python wpaa_run.py --urls https://news.ycombinator.com
```

### 2. Interactive HTML Output

```powershell
python wpaa_run.py --urls https://github.com --export-html
```

### 3. Change Tracking

```powershell
# First run (create snapshot)
python wpaa_run.py --urls https://example.com --compare-changes

# Second run (detect changes)
python wpaa_run.py --urls https://example.com --compare-changes
```

### 4. Performance-Optimized Analysis

```powershell
python wpaa_run.py --urls https://example.com --exclude script style meta --max-depth 5 --show-performance
```

## Output Files

Files generated after analysis:

- `tree_*.svg` - SVG format tree structure
- `tree_*.html` - Interactive HTML viewer
- `tree_*.csv` - CSV format data
- `tree_*.md` - Markdown report
- `cache/` - HTML cache files
- `snapshots/` - Snapshots for change tracking
