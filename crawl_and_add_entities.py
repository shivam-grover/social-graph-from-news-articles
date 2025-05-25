import os
import time
import json
import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from elasticsearch import Elasticsearch
import spacy

# --- Config
ES_INDEX = "efc_articles_1"
MAX_ARTICLES = 1000
CRAWL_TRACKER = "url_queue.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}

# --- Init ES and spaCy
es = Elasticsearch("http://localhost:9200")
nlp = spacy.load("en_core_web_trf")

# --- Utility Functions
def get_hash(content): return hashlib.md5(content.encode()).hexdigest()
def safe_id(url): return hashlib.sha1(url.encode()).hexdigest()

def deduplicate_people(names):
    names = sorted(set(names), key=lambda x: (-len(x), x))  # longer names first
    unique = []
    for name in names:
        if not any(name != other and name in other for other in unique):
            unique.append(name)
    return unique

def extract_clean_paragraph(p):
    return " ".join(p.stripped_strings)

def clean_body(body: str) -> str:
    body = re.sub(r"\n{2,}", "\n", body).strip()
    boilerplate_patterns = [
        r"Have a confidential story.*?Signal also available\.",
        r"Bear with us if you leave a comment.*?won’t\.",
        r"^Contact:.*?(Signal also available\.)?",
    ]
    for pattern in boilerplate_patterns:
        body = re.sub(pattern, "", body, flags=re.DOTALL | re.IGNORECASE)
    return re.sub(r"\n{2,}", "\n", body).strip()

def extract_entities(text):
    doc = nlp(text)
    entities = {
        "people": set(),
        "orgs": set(),
        "locations": set(),
        "dates": set()
    }
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["people"].add(ent.text.strip())
        elif ent.label_ == "ORG":
            entities["orgs"].add(ent.text.strip())
        elif ent.label_ in {"GPE", "LOC"}:
            entities["locations"].add(ent.text.strip())
        elif ent.label_ == "DATE":
            entities["dates"].add(ent.text.strip())
    entities["people"] = deduplicate_people(entities["people"])
    return {k: list(v) for k, v in entities.items()}

# --- I/O helpers
def save_url_queue(queue):
    with open(CRAWL_TRACKER, "w") as f: json.dump(list(queue), f)

def load_url_queue():
    if not os.path.exists(CRAWL_TRACKER): return set()
    with open(CRAWL_TRACKER) as f: return set(json.load(f))

def is_indexed(url):
    return es.exists(index=ES_INDEX, id=safe_id(url))

# --- Article Parsing
def parse_article(html, url):
    soup = BeautifulSoup(html, "lxml")
    title = soup.select_one("h1.article-main-title-heading")
    date = soup.select_one("span.article-header-posted-time")
    author = soup.select_one("span.article-header-author-name")
    category = soup.select_one("span.article-section-label")

    body_div = soup.select_one("div#articleDetail")
    paragraphs = body_div.find_all("p") if body_div else []
    body = "\n".join(extract_clean_paragraph(p) for p in paragraphs)
    body = clean_body(body)

    related = soup.select("div.related-articles a[href]")
    related_links = {
        urljoin("https://www.efinancialcareers.com", a['href'])
        for a in related if "/news/" in a.get('href', '')
    }

    recommended = soup.select("efc-recommended-news a[href]")
    recommended_links = {
        urljoin("https://www.efinancialcareers.com", a['href'])
        for a in recommended if "/news/" in a.get('href', '')
    }

    all_links = related_links.union(recommended_links)
    entities = extract_entities(body)

    return {
        "url": url,
        "title": title.get_text(strip=True) if title else None,
        "date": date.get_text(strip=True) if date else None,
        "author": author.get_text(strip=True) if author else None,
        "body": body,
        "category": category.get_text(strip=True) if category else None,
        "related": list(related_links),
        "recommended": list(recommended_links),
        "entities": entities,
        "hash": get_hash(body)
    }, all_links

# --- Store to Elasticsearch
def store_article(article):
    es.index(index=ES_INDEX, id=safe_id(article["url"]), document=article)

# --- Crawl logic
def crawl(start_url=None):
    visited = set()
    queue = load_url_queue()
    if start_url and start_url not in queue:
        queue.add(start_url)

    while queue and len(visited) < MAX_ARTICLES:
        url = queue.pop()
        if is_indexed(url) or url in visited:
            continue
        print(f"Crawling {url}")
        try:
            html = requests.get(url, headers=HEADERS, timeout=10).text
            data, new_links = parse_article(html, url)
            store_article(data)
            visited.add(url)

            for link in new_links:
                if not is_indexed(link) and link not in visited:
                    queue.add(link)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        save_url_queue(queue)
        time.sleep(5)

# --- Main
if __name__ == "__main__":
    if not es.indices.exists(index=ES_INDEX):
        es.indices.create(index=ES_INDEX)
    # crawl("https://www.efinancialcareers.com/news/hsbc-s-european-equity-researchers-say-it-s-worse-than-feared")
    crawl()