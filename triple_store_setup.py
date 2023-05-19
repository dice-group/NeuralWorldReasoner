"""
# Tools for Jena.
wget https://archive.apache.org/dist/jena/binaries/apache-jena-4.7.0.tar.gz

# SPARQL Server creation.
wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-4.7.0.tar.gz

# Unzip files
tar -xzf apache-jena-fuseki-4.7.0.tar.gz
tar -xzf apache-jena-4.7.0.tar.gz

# Create folder for triple-store
mkdir -p databases/family/

# Ensure that the example database is also in the working directory
(base) demir@demir:~/Desktop/Softwares/DXAI/Fuseki$ ls
apache-jena-4.7.0         apache-jena-fuseki-4.7.0         databases
apache-jena-4.7.0.tar.gz  apache-jena-fuseki-4.7.0.tar.gz  family.nt


# Ensure that the JAVA_HOME is set to /usr/lib/jvm/java-1.17.0-openjdk-amd64

(base) demir@demir:~/Desktop/Softwares/DXAI/Fuseki$ apache-jena-4.7.0/bin/tdb2.tdbloader --loader=parallel --loc databases/family/ family.nt
09:16:40 INFO  loader          :: Loader = LoaderParallel
09:16:40 INFO  loader          :: Start: family.nt
09:16:41 INFO  loader          :: Finished: family.nt: 2,033 tuples in 0.34s (Avg: 6,050)
09:16:41 INFO  loader          :: Finish - index OSP
09:16:41 INFO  loader          :: Finish - index SPO
09:16:41 INFO  loader          :: Finish - index POS
(base) demir@demir:~/Desktop/Softwares/DXAI/Fuseki$


# Run the Triple store
(base) demir@demir:~/Desktop/Softwares/DXAI/Fuseki/apache-jena-fuseki-4.7.0$
java -Xmx4G -jar fuseki-server.jar --tdb2 --loc=/home/demir/Desktop/Softwares/DXAI/Fuseki/databases/family /family
09:19:03 INFO  Server          :: Running in read-only mode for /family
09:19:04 INFO  Server          :: Apache Jena Fuseki 4.7.0
09:19:04 INFO  Config          :: FUSEKI_HOME=/home/demir/Desktop/Softwares/DXAI/Fuseki/apache-jena-fuseki-4.7.0/.
09:19:04 INFO  Config          :: FUSEKI_BASE=/home/demir/Desktop/Softwares/DXAI/Fuseki/apache-jena-fuseki-4.7.0/run
09:19:04 INFO  Config          :: Shiro file: file:///home/demir/Desktop/Softwares/DXAI/Fuseki/apache-jena-fuseki-4.7.0/run/shiro.ini
09:19:04 INFO  Config          :: Template file: templates/config-tdb2-dir-readonly
09:19:05 INFO  Server          :: Database: TDB2 dataset: location=/home/demir/Desktop/Softwares/DXAI/Fuseki/databases/family
09:19:05 INFO  Server          :: Path = /family
09:19:05 INFO  Server          ::   Memory: 4.0 GiB
09:19:05 INFO  Server          ::   Java:   17.0.6
09:19:05 INFO  Server          ::   OS:     Linux 5.15.0-71-generic amd64
09:19:05 INFO  Server          ::   PID:    88246
09:19:05 INFO  Server          :: Started 2023/05/19 09:19:05 CEST on port 3030

# Open Another Terminal execute the following

curl http://localhost:3030/family/ --data query=PREFIX%20rdf%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%0APREFIX%20rdfs%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0ASELECT%20%2A%20WHERE%20%7B%0A%20%20%3Fsub%20%3Fpred%20%3Fobj%20.%0A%7D%20LIMIT%2010 -X POST


# You should be getting

{ "head": {
    "vars": [ "sub" , "pred" , "obj" ]
  } ,
  "results": {
    "bindings": [
      {
        "sub": { "type": "bnode" , "value": "b0" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" } ,
        "obj": { "type": "uri" , "value": "http://www.w3.org/2002/07/owl#Ontology" }
      } ,
      {
        "sub": { "type": "uri" , "value": "http://www.benchmark.org/family#hasChild" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" } ,
        "obj": { "type": "uri" , "value": "http://www.w3.org/2002/07/owl#ObjectProperty" }
      } ,
      {
        "sub": { "type": "uri" , "value": "http://www.benchmark.org/family#hasParent" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" } ,
        "obj": { "type": "uri" , "value": "http://www.w3.org/2002/07/owl#ObjectProperty" }
      } ,
      {
        "sub": { "type": "uri" , "value": "http://www.benchmark.org/family#hasSibling" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" } ,
        "obj": { "type": "uri" , "value": "http://www.w3.org/2002/07/owl#ObjectProperty" }
      } ,
      {
        "sub": { "type": "uri" , "value": "http://www.benchmark.org/family#married" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" } ,
        "obj": { "type": "uri" , "value": "http://www.w3.org/2002/07/owl#ObjectProperty" }
      } ,
      {
        "sub": { "type": "uri" , "value": "http://www.benchmark.org/family#Brother" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" } ,
        "obj": { "type": "uri" , "value": "http://www.w3.org/2002/07/owl#Class" }
      } ,
      {
        "sub": { "type": "uri" , "value": "http://www.benchmark.org/family#Brother" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/2000/01/rdf-schema#subClassOf" } ,
        "obj": { "type": "uri" , "value": "http://www.benchmark.org/family#Male" }
      } ,
      {
        "sub": { "type": "uri" , "value": "http://www.benchmark.org/family#Brother" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/2000/01/rdf-schema#subClassOf" } ,
        "obj": { "type": "uri" , "value": "http://www.benchmark.org/family#PersonWithASibling" }
      } ,
      {
        "sub": { "type": "uri" , "value": "http://www.benchmark.org/family#Male" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" } ,
        "obj": { "type": "uri" , "value": "http://www.w3.org/2002/07/owl#Class" }
      } ,
      {
        "sub": { "type": "uri" , "value": "http://www.benchmark.org/family#Male" } ,
        "pred": { "type": "uri" , "value": "http://www.w3.org/2000/01/rdf-schema#subClassOf" } ,
        "obj": { "type": "uri" , "value": "http://www.benchmark.org/family#Person" }
      }
    ]
  }
}
"""

import requests

response = requests.post('http://localhost:3030/family/sparql', data={
    'query': 'SELECT ?s  { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.benchmark.org/family#Brother>}'})
# Adding brackets
results = {'<'+i['s']['value']+'>' for i in response.json()['results']['bindings']}
print(results)
