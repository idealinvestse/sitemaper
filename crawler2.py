import requests
from bs4 import BeautifulSoup, Comment
import os
import json
import hashlib
import logging
import time
from argparse import ArgumentParser
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_parser():
    parser = ArgumentParser(description="Web Crawler for extracting information from websites")
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument("--output", default="output", help="Base directory for output files")
    parser.add_argument("--depth", type=int, default=1, help="Depth of crawl")
    parser.add_argument("--rate-limit", type=float, default=1.0, help="Time delay between requests in seconds")
    parser.add_argument("--user-agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64)", help="Custom User-Agent string")
    parser.add_argument("--max-links-per-page", type=int, default=10, help="Maximum number of links to follow per page")
    parser.add_argument("--exclude-paths", default="", help="Comma-separated list of paths to exclude from crawling")
    parser.add_argument("--http-method", default="GET", help="HTTP method to use for requests")
    return parser

def create_output_directory(base_path, domain):
    """ Creates a directory for the domain if it does not exist. """
    sanitized_domain = hashlib.md5(domain.encode()).hexdigest()
    path = os.path.join(base_path, sanitized_domain)
    os.makedirs(path, exist_ok=True)
    return path

def fetch_url(url, user_agent, http_method):
    headers = {'User-Agent': user_agent}
    try:
        response = requests.request(http_method, url, headers=headers)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

def parse_html(response):
    """ Parses the HTML content from a response object """
    return BeautifulSoup(response.text, 'html.parser')

def clean_text_elements(elements):
    """ Clean and filter text elements from the page """
    return [element.strip() for element in elements if element.strip() and not isinstance(element, (Comment, type(None)))]

def is_internal_link(domain, url):
    """ Checks if a given URL is internal to the domain """
    return urlparse(url).netloc == domain

def save_data(output_directory, url, data):
    """ Saves crawled data to a JSON file """
    filename = hashlib.md5(url.encode()).hexdigest() + '.json'
    filepath = os.path.join(output_directory, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def crawl(url, depth, output_directory, visited, user_agent, rate_limit, max_links_per_page, exclude_paths, http_method, stats):
    if depth == 0 or url in visited:
        return
    visited.add(url)
    logging.info(f"Crawling: {url}")
    time.sleep(rate_limit)
    response = fetch_url(url, user_agent, http_method)
    if not response:
        stats['errors'] += 1
        return
    stats['pages_crawled'] += 1
    soup = parse_html(response)
    page_data = {
        'metadata': {'url': url, 'title': soup.title.string if soup.title else 'Untitled'},
        'text_elements': clean_text_elements(soup.find_all(string=True)),
        'image_links': [urljoin(url, img.get('src', '')) for img in soup.find_all('img') if img.get('src')]
    }
    save_data(output_directory, url, page_data)
    links_followed = 0
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('mailto:') or href.startswith('javascript:') or any(href.startswith(ex) for ex in exclude_paths):
            continue
        next_url = urljoin(url, href)
        if is_internal_link(urlparse(url).netloc, next_url) and links_followed < max_links_per_page:
            crawl(next_url, depth-1, output_directory, visited, user_agent, rate_limit, max_links_per_page, exclude_paths, http_method, stats)
            links_followed += 1
    stats['links_found'] += links_followed
    logging.info(f"Progress: {stats['pages_crawled']} pages crawled, {stats['links_found']} links found, {stats['errors']} errors.")

def main():
    parser = setup_parser()
    args = parser.parse_args()
    domain = urlparse(args.url).netloc
    output_directory = create_output_directory(args.output, domain)
    visited = set()
    stats = {'pages_crawled': 0, 'links_found': 0, 'errors': 0}
    exclude_paths = args.exclude_paths.split(',') if args.exclude_paths else []
    crawl(args.url, args.depth, output_directory, visited, args.user_agent, args.rate_limit, args.max_links_per_page, exclude_paths, args.http_method, stats)

if __name__ == "__main__":
    main()