import argparse
import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from anytree import Node, RenderTree
from anytree.exporter import DotExporter, JsonExporter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging
import time
import os
import json
from functools import wraps

from tree_comparison import TreeComparator
from output_formats import OutputFormatter
from performance_optimizer import get_optimizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"{func.__name__} error: {e}")
            return None
    return wrapper

def load_cache(url, cache_dir="cache"):
    cache_file = os.path.join(cache_dir, f"{hash(url)}.html")
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            logging.info(f"Cache loaded: {url}")
            return f.read()
    return None

def save_cache(url, html, cache_dir="cache"):
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = os.path.join(cache_dir, f"{hash(url)}.html")
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(html)
    logging.info(f"Cached HTML: {url}")

async def fetch_html(session, url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                save_cache(url, html)
                return html
        except Exception as e:
            logging.warning(f"Fetch failed {url} (attempt {attempt + 1}/{retries}): {e}")
            await asyncio.sleep(delay)
    logging.error(f"Failed to fetch HTML: {url}")
    return None

@handle_errors
def get_dynamic_html(url):
    options = Options()
    options.headless = True
    try:
        service = Service()
    except:
        service = Service('/path/to/chromedriver')
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(2)
    html = driver.page_source
    driver.quit()
    save_cache(url, html)
    return html

@handle_errors
def parse_html(html):
    return BeautifulSoup(html, 'html.parser')

def build_tree(soup, parent=None, exclude_tags=None, include_attrs=None, custom_filter=None, max_depth=None, current_depth=0, include_text=False):
    if max_depth is not None and current_depth > max_depth:
        return
    children = soup.select(custom_filter) if custom_filter else soup.children
    for child in children:
        if hasattr(child, 'name') and child.name and (exclude_tags is None or child.name not in exclude_tags):
            node_name = child.name
            if include_attrs:
                for attr in include_attrs:
                    if child.get(attr):
                        node_name += f" ({attr}={child[attr]})"
            node = Node(node_name, parent=parent)
            if include_text and child.string and child.string.strip():
                Node(f"TEXT: {child.string.strip()}", parent=node)
            build_tree(child, node, exclude_tags, include_attrs, custom_filter, max_depth, current_depth + 1, include_text)

def print_tree(root):
    logging.info("Tree structure:")
    for pre, _, node in RenderTree(root):
        logging.info(f"{pre}{node.name}")

def print_json_tree(root):
    json_tree = JsonExporter().export(root)
    logging.info("JSON tree:")
    logging.info(json_tree)

@handle_errors
def visualize_tree(root, filename="web_structure"):
    DotExporter(root).to_picture(f"{filename}.png")
    logging.info(f"Tree saved as {filename}.png")

@get_optimizer().performance_monitor
async def analyze_url(url, args):
    optimizer = get_optimizer()
    
    cache_key = optimizer.cache_manager.get_cache_key(url, {
        'use_selenium': args.use_selenium,
        'exclude': args.exclude,
        'include_attrs': args.include_attrs,
        'custom_filter': args.custom_filter,
        'max_depth': args.max_depth,
        'include_text': args.include_text
    })
    
    cached_result = optimizer.cache_manager.get(cache_key)
    if cached_result:
        logging.info(f"Cache hit: {url}")
        return cached_result
        html = load_cache(url)
    if not html:
        if args.use_selenium:
            html = get_dynamic_html(url)
        else:
            async with aiohttp.ClientSession() as session:
                html = await fetch_html(session, url)
    if not html:
        return None

    soup = parse_html(html)
    if not soup:
        return None

    root = Node(soup.name or "root")
    build_tree(soup, root, args.exclude, args.include_attrs, args.custom_filter, args.max_depth, include_text=args.include_text)
    
    if hasattr(args, 'optimize_tree') and args.optimize_tree:
        pass
    
    root.node_count = len([root] + list(root.descendants))
    
    if args.output == 'text':
        print_tree(root)
    elif args.output == 'json':
        print_json_tree(root)
    
    formatter = OutputFormatter()
    if hasattr(args, 'export_svg') and args.export_svg:
        formatter.export_to_svg(root, f"tree_{hash(url)}.svg")
    if hasattr(args, 'export_html') and args.export_html:
        formatter.export_to_interactive_html(root, f"tree_{hash(url)}.html")
    if hasattr(args, 'export_csv') and args.export_csv:
        formatter.export_to_csv(root, f"tree_{hash(url)}.csv")
    if hasattr(args, 'export_markdown') and args.export_markdown:
        formatter.export_to_markdown(root, f"tree_{hash(url)}.md")
    
    if args.visualize:
        visualize_tree(root)
    
    if hasattr(args, 'compare_changes') and args.compare_changes:
        comparator = TreeComparator()
        diff = comparator.detect_changes(url, root)
        if diff:
            print(comparator.generate_diff_report(diff))
    
    optimizer.cache_manager.set(cache_key, root)
    
    return root

async def main(args):
    optimizer = get_optimizer()
    
    try:
        if len(args.urls) > 1:
            results = await optimizer.batch_process_urls(args.urls, analyze_url, args.__dict__)
            logging.info(f"Analysis completed: {len(results)} URLs")
        else:
            result = await analyze_url(args.urls[0], args)
            if result:
                logging.info("Analysis completed")
        
        if hasattr(args, 'show_performance') and args.show_performance:
            report = optimizer.get_performance_report()
            print("\n=== Performance Report ===")
            print(json.dumps(report, indent=2, ensure_ascii=False))
            
    finally:
        optimizer.cleanup()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Web Page Architecture Analyzer - Analyze HTML structure as tree")
    parser.add_argument('--urls', nargs='+', required=True, help="Target URLs")
    parser.add_argument('--use-selenium', action='store_true', help="Use Selenium for dynamic content")
    parser.add_argument('--exclude', nargs='*', help="Exclude tags (e.g., script style)")
    parser.add_argument('--include-attrs', nargs='*', help="Include attributes (e.g., class id href)")
    parser.add_argument('--custom-filter', help="CSS selector filter")
    parser.add_argument('--max-depth', type=int, help="Maximum tree depth")
    parser.add_argument('--include-text', action='store_true', help="Include text content")
    parser.add_argument('--output', choices=['text', 'json'], default='text', help="Output format")
    parser.add_argument('--visualize', action='store_true', help="Generate PNG visualization")
    
    parser.add_argument('--export-svg', action='store_true', help="Export as SVG")
    parser.add_argument('--export-html', action='store_true', help="Export as interactive HTML")
    parser.add_argument('--export-csv', action='store_true', help="Export as CSV")
    parser.add_argument('--export-markdown', action='store_true', help="Export as Markdown")    
    parser.add_argument('--compare-changes', action='store_true', help="Compare with previous version")
    parser.add_argument('--show-performance', action='store_true', help="Show performance metrics")
    parser.add_argument('--optimize-tree', action='store_true', help="Optimize tree structure")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(main(args))