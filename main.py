from reasoners import NWR, CWR, SPARQLCWR, NC, AbstractReasoner, AbstractDLConcept, Restriction
from util import jaccard_similarity, compute_prediction, evaluate_results
import time
from dicee import KGE
import pandas as pd
import torch

pd.set_option("display.precision", 4)
pd.pandas.set_option('display.max_columns', None)

# (1) Load the model
pretrained_model = KGE("Experiments/2023-05-16 10:51:31.694192")

# (3) All entities \domain^\interperation
entities = list(pretrained_model.entity_to_idx.keys())
# (4) Read a knowledge base
kg = pd.read_csv('KGs/Family/train.txt', sep="\s+", header=None, usecols=[0, 1, 2],
                 names=['subject', 'relation', 'object'], dtype=str)
# (5) Retrieve a set of all named individuals
all_named_individuals = set(kg[(kg['relation'] == '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') & (
        kg['object'] == '<http://www.w3.org/2002/07/owl#NamedIndividual>')]['subject'].tolist())

# (6) Named classes.
all_named_concepts = set(kg[(kg['relation'] == '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') & (
        kg['object'] == '<http://www.w3.org/2002/07/owl#Class>')]['subject'].tolist())

assert len(all_named_concepts) == len(list(all_named_concepts))
# Order Matters at testing time.
all_named_concepts = [NC(i) for i in all_named_concepts]

swr = SPARQLCWR(url='http://localhost:3030/family/sparql', name='Fuseki')

relations=swr.query("SELECT DISTINCT ?var WHERE { ?subject ?p <http://www.w3.org/2002/07/owl#NamedIndividual> .?subject ?var ?object .}")

neural_kb = NWR(predictor=pretrained_model, gamma=0.25, all_named_individuals=all_named_individuals)
cwr = CWR(database=kg, all_named_individuals=all_named_individuals)
# Create Negations
neg_named_concepts = [i.neg() for i in all_named_concepts]

existential_res=[]
universal_res=[]
for role_iri in relations:
    for filler in all_named_concepts:
        existential_res.append(Restriction(opt='∃', role=role_iri, filler=filler))
        universal_res.append(Restriction(opt='∀', role=role_iri, filler=filler))
# Un
df= evaluate_results(true_results=compute_prediction(universal_res, predictor=cwr),
                        predictions=compute_prediction(universal_res, predictor=swr))


assert evaluate_results(true_results=compute_prediction(existential_res, predictor=cwr),
                        predictions=compute_prediction(existential_res, predictor=swr))['Similarity'].mean() == 1.0

exit(1)
# Evaluate on all NC.
assert evaluate_results(true_results=compute_prediction(all_named_concepts, predictor=cwr),
                        predictions=compute_prediction(all_named_concepts, predictor=swr))['Similarity'].mean() == 1.0
assert evaluate_results(true_results=compute_prediction(neg_named_concepts, predictor=cwr),
                        predictions=compute_prediction(neg_named_concepts, predictor=swr))['Similarity'].mean() == 1.0
# Create Unions and Intersections
unions = []
intersections = []
for i in all_named_concepts:
    for j in all_named_concepts:
        unions.append(i.union(j))
        intersections.append(i.intersection(j))
#

assert evaluate_results(true_results=compute_prediction(intersections, predictor=cwr),
                        predictions=compute_prediction(intersections, predictor=swr))['Similarity'].mean() == 1.0
assert evaluate_results(true_results=compute_prediction(unions, predictor=cwr),
                        predictions=compute_prediction(unions, predictor=swr))['Similarity'].mean() == 1.0


print(jaccard_similarity(y=cwr.existential_restriction(role='<http://www.benchmark.org/family#married>',
                                                       filler_concept='<http://www.benchmark.org/family#Female>'),
                         yhat=nwr.existential_restriction(role='<http://www.benchmark.org/family#married>',
                                                          filler_concept='<http://www.benchmark.org/family#Female>')))

print('Jaccard(CWR(Female ⊓ Sister),NWR(Female ⊓ Sister)):',
      jaccard_similarity(
          y=cwr.conjunction('<http://www.benchmark.org/family#Female>', '<http://www.benchmark.org/family#Sister>'),
          yhat=nwr.conjunction('<http://www.benchmark.org/family#Female>',
                               '<http://www.benchmark.org/family#Sister>')))

print('Jaccard(CWR(Female ⊔ Sister),NWR(Female ⊔ Sister)):',
      jaccard_similarity(
          y=cwr.disjunction('<http://www.benchmark.org/family#Female>', '<http://www.benchmark.org/family#Sister>'),
          yhat=nwr.disjunction('<http://www.benchmark.org/family#Female>',
                               '<http://www.benchmark.org/family#Sister>')))
