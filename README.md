# WPAA: WebPage Architecture Analyzer

EN | [KR](docs/README_KR.md)

WPAA is a comprehensive tool for analyzing and visualizing HTML architecture of web pages. It provides tree-structured visualization for both static and dynamic web pages, making DOM structure analysis intuitive and efficient.

## Key Features

- 🌳 **Tree Visualization**: Hierarchical representation of HTML structure
- 🔄 **Change Detection**: Automatic detection and comparison of webpage structure changes
- 🌐 **Web Interface**: Intuitive web UI for easy analysis
- 📊 **Multiple Export Formats**: Support for SVG, interactive HTML, CSV, and Markdown
- ⚡ **Performance Optimization**: Asynchronous processing, caching, and memory optimization
- 🔧 **Static/Dynamic Analysis**: Support for JavaScript-rendered web pages
- 🎯 **Custom Filtering**: CSS selector and attribute filtering capabilities
- 📈 **Performance Monitoring**: Track execution time, memory usage, and cache efficiency

## Installation

[Setup Guide](docs/SETUP.md)

### Requirements

```
Python 3.7+
pip install -r requirements.txt
```

**Required External Programs:**

1. **Graphviz Installation**:
   - Download installer from [official website](https://graphviz.org/download/)
   - Add bin directory to system PATH (e.g., `C:\Program Files\Graphviz\bin`)

2. **ChromeDriver Installation** (for dynamic page analysis):
   - Download from [ChromeDriver website](https://sites.google.com/a/chromium.org/chromedriver/downloads)
   - Save to appropriate location and update path in code:
     ```python
     service = Service('your/path/to/chromedriver')
     ```

## Usage

### 1. Web Interface (Recommended)

```bash
python run_web_interface.py
```

Access `http://127.0.0.1:5000` in your browser for intuitive web-based analysis.

**Web Interface Features:**
- 📱 User-friendly web UI
- 🔄 Real-time analysis progress display
- 📊 Download various output formats
- 🔍 Change comparison functionality
- 📈 Performance statistics

### 2. Command Line Interface

Basic usage:
```bash
python wpaa_run.py --urls https://example.com
```

Advanced options:
```bash
python wpaa_run.py --urls https://example.com https://test.com \
  --exclude script style \
  --include-attrs class href \
  --custom-filter "div.content" \
  --max-depth 3 \
  --export-html \
  --compare-changes \
  --show-performance
```

## Command Line Options

- `--urls`: List of webpage URLs to analyze (required)
- `--use-selenium`: Use Selenium for dynamic content fetching
- `--exclude`: HTML tags to exclude (e.g., script style)
- `--include-attrs`: HTML attributes to include in nodes (e.g., class id href)
- `--custom-filter`: Filter specific elements using CSS selectors (e.g., div.classname)
- `--max-depth`: Limit maximum tree depth
- `--include-text`: Include text content
- `--output`: Choose output format (text or json)
- `--visualize`: Visualize tree structure as PNG file
- `--export-svg`: Export to SVG format
- `--export-html`: Export to interactive HTML
- `--export-csv`: Export to CSV format
- `--export-markdown`: Export to Markdown format
- `--compare-changes`: Compare with previous version
- `--show-performance`: Display performance report
- `--optimize-tree`: Optimize tree structure

## Examples

### Basic Analysis
```bash
python wpaa_run.py --urls https://news.ycombinator.com
```

### Dynamic Content Analysis (Using Selenium)
```bash
python wpaa_run.py --urls https://www.example.com --use-selenium
```

### Exclude Specific Tags and Visualize
```bash
python wpaa_run.py --urls https://www.example.com --exclude script style meta link --visualize
```

### Include Specific Attributes and JSON Output
```bash
python wpaa_run.py --urls https://www.example.com --include-attrs class id href --output json
```

### Interactive HTML with Change Comparison
```bash
python wpaa_run.py --urls https://www.example.com --export-html --compare-changes --show-performance
```

### Export to Multiple Formats
```bash
python wpaa_run.py --urls https://www.example.com --export-svg --export-csv --export-markdown
```

## Architecture Overview

- **Caching**: Performance optimization for repeated URL analysis
- **Asynchronous Processing**: Concurrent analysis of multiple URLs
- **Error Handling**: Consistent error handling through decorators
- **Tree Structure**: HTML DOM visualization using anytree library

## Development History
MK-II_2523: Feature improvements completed
- [X] Tree comparison functionality for detecting site changes
- [X] Web interface implementation
- [X] Support for more output formats (SVG, interactive HTML)
- [X] Performance optimization and memory usage improvements