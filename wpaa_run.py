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

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 에러 처리 데코레이터
def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"{func.__name__}에서 오류 발생: {e}")
            return None
    return wrapper

# 1. 캐싱된 HTML 로드/저장
def load_cache(url, cache_dir="cache"):
    cache_file = os.path.join(cache_dir, f"{hash(url)}.html")
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            logging.info(f"{url}에 대한 캐시를 로드합니다.")
            return f.read()
    return None

def save_cache(url, html, cache_dir="cache"):
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = os.path.join(cache_dir, f"{hash(url)}.html")
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(html)
    logging.info(f"{url}의 HTML을 캐시에 저장했습니다.")

# 2. 비동기 HTML 가져오기
async def fetch_html(session, url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                save_cache(url, html)
                return html
        except Exception as e:
            logging.warning(f"{url} 가져오기 실패 (시도 {attempt + 1}/{retries}): {e}")
            await asyncio.sleep(delay)
    logging.error(f"{url}의 HTML을 가져오지 못했습니다.")
    return None

# 3. 동적 콘텐츠 가져오기 (Selenium)
@handle_errors
def get_dynamic_html(url):
    options = Options()
    options.headless = True
    service = Service('/path/to/chromedriver')  # ChromeDriver 경로 설정
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(2)  # 페이지 로딩 대기
    html = driver.page_source
    driver.quit()
    save_cache(url, html)
    return html

# 4. HTML 파싱
@handle_errors
def parse_html(html):
    return BeautifulSoup(html, 'html.parser')

# 5. 트리 생성 (성능 최적화 및 커스텀 필터링)
def build_tree(soup, parent=None, exclude_tags=None, include_attrs=None, custom_filter=None, max_depth=None, current_depth=0, include_text=False):
    if max_depth is not None and current_depth > max_depth:
        return
    # 커스텀 필터링이 있을 경우 select 사용
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

# 6. 출력 함수
def print_tree(root):
    logging.info("트리 구조:")
    for pre, _, node in RenderTree(root):
        logging.info(f"{pre}{node.name}")

def print_json_tree(root):
    json_tree = JsonExporter().export(root)
    logging.info("JSON 형식 트리:")
    logging.info(json_tree)

@handle_errors
def visualize_tree(root, filename="web_structure"):
    DotExporter(root).to_picture(f"{filename}.png")
    logging.info(f"트리가 {filename}.png로 저장되었습니다.")

# 7. 메인 로직
async def analyze_url(url, args):
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

    if args.output == 'text':
        print_tree(root)
    elif args.output == 'json':
        print_json_tree(root)
    if args.visualize:
        visualize_tree(root)
    return root

async def main(args):
    tasks = [analyze_url(url, args) for url in args.urls]
    await asyncio.gather(*tasks)

# 8. 명령줄 인자 설정
def parse_arguments():
    parser = argparse.ArgumentParser(description="웹 페이지의 HTML 구조를 분석하여 트리 형태로 표현합니다.")
    parser.add_argument('--urls', nargs='+', required=True, help="분석할 웹 페이지 URL 목록")
    parser.add_argument('--use-selenium', action='store_true', help="Selenium으로 동적 콘텐츠 가져오기")
    parser.add_argument('--exclude', nargs='*', help="제외할 태그 목록 (예: script style)")
    parser.add_argument('--include-attrs', nargs='*', help="노드에 포함할 속성 (예: class id href)")
    parser.add_argument('--custom-filter', help="커스텀 CSS 셀렉터로 필터링 (예: div.classname)")
    parser.add_argument('--max-depth', type=int, help="트리의 최대 깊이")
    parser.add_argument('--include-text', action='store_true', help="텍스트 콘텐츠 포함")
    parser.add_argument('--output', choices=['text', 'json'], default='text', help="출력 형식")
    parser.add_argument('--visualize', action='store_true', help="PNG로 시각화")
    return parser.parse_args()

# 실행
if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(main(args))