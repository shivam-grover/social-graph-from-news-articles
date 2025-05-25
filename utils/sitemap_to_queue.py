import json
import xml.etree.ElementTree as ET

SITEMAP_FILE = "../sitemaps/news-archive-current.xml"        # Your sitemap XML file
# SITEMAP_FILE = "recent-news-sitemap.xml"        # Your sitemap XML file
QUEUE_FILE = "../sitemaps/url_queue.json"       # Output queue file

def extract_urls_from_sitemap(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = [url.find('ns:loc', namespace).text for url in root.findall('ns:url', namespace)]
    return urls

def save_to_queue(urls, queue_file):
    with open(queue_file, "w") as f:
        json.dump(urls, f, indent=2)

if __name__ == "__main__":
    urls = extract_urls_from_sitemap(SITEMAP_FILE)
    save_to_queue(urls, QUEUE_FILE)
    print(f"Saved {len(urls)} URLs to {QUEUE_FILE}")