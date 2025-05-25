from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

print("Elasticsearch info:")
print(es.info())

index_name = "test_articles"

# Ensure index exists
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name)
    print(f"✅ Created index: {index_name}")
else:
    print(f"✅ Index already exists: {index_name}")

# Test document
doc = {"title": "Test", "body": "Hello ES"}
es.index(index=index_name, id="test1", document=doc)

# Check existence
print("✅ Document exists:", es.exists(index=index_name, id="test1"))