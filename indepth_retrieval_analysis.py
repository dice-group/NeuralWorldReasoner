import requests
from dicee import KGE
from reasoners import HermiT, NWR, SPARQLCWR, NC, Restriction, ValueRestriction
from util import compute_prediction, evaluate_results
import time
from dicee import KGE
import pandas as pd
import torch

pd.set_option("display.precision", 4)
pd.pandas.set_option('display.max_columns', None)

# (1) Load the model
pretrained_model = KGE("Experiments/2023-05-24 11:53:06.006435")
# (2) Build a SPARQL connection.
swr = SPARQLCWR(url='http://localhost:3030/family/sparql', name='Fuseki')
hermit = HermiT(url='http://localhost:8080/hermit')

# (3) Get all named classes/concepts.
all_named_concepts = swr.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                               "SELECT DISTINCT ?var\n"
                               "WHERE {?var a owl:Class.}")
# (4) Get all named individuals.
all_named_individuals = swr.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                                  "SELECT DISTINCT ?var\n"
                                  "WHERE {?var a owl:NamedIndividual.}")
neural_kb = NWR(predictor=pretrained_model, gammas={'NC': 0.1, 'Exists': 0.7, 'Forall': 0.01, 'Value': 0.5},
                all_named_individuals=all_named_individuals)



# (5) Get all roles.
relations = swr.query(
    "SELECT DISTINCT ?var WHERE { ?subject ?p <http://www.w3.org/2002/07/owl#NamedIndividual> .?subject ?var ?object .}")
# (5.1) Remove the type
relations.remove('<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>')
relations = list(relations)
# (6) Concept Creation: Create  atomic concepts, negations, unions ..
# Order Matters at testing time.
all_named_concepts = [NC(i) for i in all_named_concepts]

for i in all_named_concepts:
    print(f"{i.str}\t{i.manchester_str}")
    y_swr=swr.predict(i)

    y_hermit=hermit.predict(i)

    print(len(y_swr),len(y_hermit),y_swr==y_hermit)


print(requests.post('http://localhost:8080/hermit', data='hasSibling SOME (Female)').json())


print(requests.post('http://localhost:8080/hermit', data='Person').json())
print(requests.post('http://localhost:8080/hermit', data='Male').json())
print(requests.post('http://localhost:8080/hermit', data='Female').json())
print(requests.post('http://localhost:8080/hermit', data='Father').json())
print(requests.post('http://localhost:8080/hermit', data='Mother').json())

print(requests.post('http://localhost:8080/hermit', data='hasSibling SOME Mother').json())
print(requests.post('http://localhost:8080/hermit', data='married SOME Sister').json())
print(requests.post('http://localhost:8080/hermit', data='hasParent SOME Mother').json())
print(requests.post('http://localhost:8080/hermit', data='hasChild SOME Father').json())
print(requests.post('http://localhost:8080/hermit', data='hasSibling VALUE F10F175').json())
print(requests.post('http://localhost:8080/hermit', data='hasSibling MIN 1').json())
print(requests.post('http://localhost:8080/hermit', data='Father AND hasSibling ONLY').json())
print(requests.post('http://localhost:8080/hermit', data='Person THAT hasChild ONLYSOME [Person]').json())
print(requests.post('http://localhost:8080/hermit', data='Person THAT hasChild SOME').json())
