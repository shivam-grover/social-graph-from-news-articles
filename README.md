# Social Graph From News Articles

This framework crawls financial news articles, extracts named entities (people, organizations, etc.), analyzes co-occurrence relationships, and visualizes these as interactive social graphs. It uses Elasticsearch for storage, and visualization using Pyvis, Matplotlib, and Neo4j.

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/shivam-grover/social-graph-from-news-articles
cd social-graph-from-news-articles
```

**NOTE:** You may skip everything else, and simply open `person_person_graph_min_count_total_2.html` and the other `html` files in the root directory to visualise the interactive graphs. It should work out of the box.

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Also Install and Configure spaCy with Transformer Model

Follow spaCy installation instructions for your platform: [https://spacy.io/usage]([url](https://spacy.io/usage))

As an example for Linux with CUDA 12:
```bash
pip install -U pip setuptools wheel
pip install -U 'spacy[cuda12x]'
python -m spacy download en_core_web_trf
```

### 3. Set Up Elasticsearch
```bash
docker run -d --name elasticsearch -e "discovery.type=single-node" -p 9200:9200 elasticsearch:8.12.0
```
Make sure it's accessible at `http://localhost:9200`


## How to Run

### Step 1: Crawl Articles and Extract Entities
```bash
python crawl_and_add_entities.py
```
This will fetch articles, extract people/orgs/locations/dates, and save the data in Elasticsearch.

### Step 2: Analyze and Visualize Graphs
Open and run `analyse_relationships.ipynb`. There you can Aggregate statistics, Generate bar plots, Create static and interactive graphs.

### Step 3: Upload Data to Neo4j
First Run Neo4j in Docker

```bash
docker run \
  --name neo4j \
  -p7474:7474 -p7687:7687 \
  -d \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.13
```

Ensure Neo4j is running and accessible at `bolt://localhost:7687`.

Edit the credentials in `build_Neo4j_graph.py` (Neo4j / password) if needed, then run:

```bash
python build_Neo4j_graph.py
```
This will create nodes for people and organizations, and relationships for co-occurrence and association.

Below are some sample queries you can run in Neo4j
```bash
1. Person to Organization associations
MATCH (p:Person)-[r:ASSOCIATED_WITH]->(o:Organization)
RETURN p, r, o
LIMIT 100;

-- 2. Top person-to-person co-occurrences
CALL {
  MATCH (p1:Person)-[r:MENTIONS]->(p2:Person)
  WHERE id(p1) < id(p2)
  RETURN p1, p2, r
  ORDER BY r.weight DESC
  LIMIT 500
}
RETURN p1, p2, r;

-- 3. Who is connected to Citi?
MATCH (o:Organization)
WHERE o.name IN ["Citi"]
WITH collect(o) AS targetOrgs
UNWIND targetOrgs AS org
MATCH (p:Person)-[r:ASSOCIATED_WITH]->(org)
RETURN DISTINCT p, r, org;

-- 4. Who co-occurs with "Alexander Phillips"?
MATCH (p:Person {name: "Alexander Phillips"})-[r:MENTIONS]-(other:Person)
RETURN p, r, other
ORDER BY r.count DESC
LIMIT 50;

-- 5. Get all orgs connected to a person
MATCH (p:Person {name: "Ray Dalio"})-[:ASSOCIATED_WITH]->(o:Organization)
RETURN p, o;

-- 6. Common connections between two people
MATCH (p:Person)
WHERE p.name IN ["Donald Trump", "David Solomon"]
SET p:Highlighted;

MATCH (t:Person {name: "Donald Trump"})-[r1:MENTIONS]-(shared:Person)-[r2:MENTIONS]-(d:Person {name: "David Solomon"})
WITH shared, r1, r2, t, d, (r1.count + r2.count) AS total_mentions
ORDER BY total_mentions DESC
LIMIT 100
RETURN shared, r1, r2, t, d;

MATCH (p:Person:Highlighted)
WHERE p.name IN ["Donald Trump", "David Solomon"]
REMOVE p:Highlighted;

-- 7. Shortest path between person and org
MATCH (p:Person {name: "Alexander Phillips"}), (o:Organization {name: "KPMG"})
MATCH path = shortestPath(
  (p)-[:MENTIONS|ASSOCIATED_WITH*..4]-(o)
)
WHERE all(n IN nodes(path)[1..-1] WHERE n:Person OR n = o)
RETURN path;

-- 8. Check connections between "Trump" and others
UNWIND ["Elon Musk", "Jamie Dimon", "John Curtice"] AS name
MATCH (p:Person {name: name})
SET p:ImportantPerson;

MATCH (p:Person {name: "Trump"})-[r:MENTIONS]-(colleague:Person)
SET p:PIVOT
RETURN p, r, colleague
ORDER BY r.count DESC;
```



