# Neural Description Logic Reasoning over incomplete Knowledge Base

# Installation
```
conda create -n nrw python=3.9 --no-default-packages && conda activate nrw
pip3 install deeponto==0.8.5
pip3 install dicee
```

## Installation Triple-store
```
mkdir Fuseki && cd Fuseki
# Install Jena 
wget https://archive.apache.org/dist/jena/binaries/apache-jena-4.7.0.tar.gz
# Install Jena-Fuseki.
wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-4.7.0.tar.gz
# Unzip files
tar -xzf apache-jena-fuseki-4.7.0.tar.gz
tar -xzf apache-jena-4.7.0.tar.gz
# Create folder for triple-store
mkdir -p Fuseki/apache-jena-fuseki-4.7.0/databases/family/

# Loading
Fuseki/apache-jena-4.7.0/bin/tdb2.tdbloader --loader=parallel --loc Fuseki/apache-jena-fuseki-4.7.0/databases/family/databases/family/ KGs/Family/Family.owl
13:08:43 INFO  loader          :: Loader = LoaderParallel
13:08:43 INFO  loader          :: Start: KGs/Family/Family.owl
13:08:43 INFO  loader          :: Finished: KGs/Family/Family.owl: 2,032 tuples in 0.63s (Avg: 3,215)
13:08:44 INFO  loader          :: Finish - index SPO
13:08:44 INFO  loader          :: Finish - index OSP
13:08:44 INFO  loader          :: Finish - index POS
13:08:44 INFO  loader          :: Time = 1.004 seconds : Triples = 2,032 : Rate = 2,024 /s

# Launching a triple store
cd Fuseki/apache-jena-fuseki-4.7.0 && java -Xmx4G -jar fuseki-server.jar --tdb2 --loc=databases/family /family

### Send a query to the triple store
curl http://localhost:3030/family/ --data query=PREFIX%20rdf%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%0APREFIX%20rdfs%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0ASELECT%20%2A%20WHERE%20%7B%0A%20%20%3Fsub%20%3Fpred%20%3Fobj%20.%0A%7D%20LIMIT%2010 -X POST
```
You can also use python to query the triple store.
```python
import requests
response = requests.post('http://localhost:3030/family/sparql', data={
    'query': 'SELECT ?s  { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.benchmark.org/family#Brother>}'})
print({'<'+i['s']['value']+'>' for i in response.json()['results']['bindings']})
```

