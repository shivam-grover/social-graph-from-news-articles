import re
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
INDEX = "efc_articles"

HIGHLIGHT = "\033[93m"  # yellow
RESET = "\033[0m"

def fix_spacing_issues(text):
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)

def find_issues_with_context(text, context=30):
    pattern = re.compile(r"[a-z]{2,}[A-Z][a-z]*")
    ignorelist = {
        "eFinancialCareers", "LinkedIn", "iPhone", "eBay", "PayPal", "YouTube",
        "WhatsApp", "iOS", "eCommerce", "OpenAI"  # Add more brand names as needed
    }

    matches = []
    for match in pattern.finditer(text):
        word = match.group(0)
        if word in ignorelist:
            continue  # skip known legit camelCase names

        start, end = match.span()
        snippet = (
            text[max(0, start - context):start]
            + HIGHLIGHT + word + RESET
            + text[end:end + context]
        )
        matches.append(snippet)

    return matches

def process_doc(doc_id, doc):
    title = doc.get("title", "")
    body = doc.get("body", "")

    title_issues = find_issues_with_context(title)
    body_issues = find_issues_with_context(body)

    if not title_issues and not body_issues:
        return False  # no problems

    print("\n--- Document:", doc["url"])
    
    if title_issues:
        print("🔹 Title Issues:")
        print("Original Title:", title)
        for snippet in title_issues:
            print("  ...", snippet, "...")

    if body_issues:
        print("🔹 Body Issues:")
        for snippet in body_issues:
            print("  ...", snippet, "...")

    choice = input("\nApply fix and update? [y/n]: ").strip().lower()
    if choice == "y":
        doc["title"] = fix_spacing_issues(title)
        doc["body"] = fix_spacing_issues(body)
        es.update(index=INDEX, id=doc_id, doc={"title": doc["title"], "body": doc["body"]})
        print("✅ Updated.")
    else:
        print("❌ Skipped.")

    return True

def run():
    query = {"match_all": {}}
    page = es.search(index=INDEX, query=query, size=1000)

    for hit in page["hits"]["hits"]:
        doc_id = hit["_id"]
        doc = hit["_source"]
        process_doc(doc_id, doc)

if __name__ == "__main__":
    run()
