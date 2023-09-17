"""
Description Logic Concept Retrieval in an open-world setting

Baseline: An OWL Reasoner HermiT
Our Approach: A neural link predictor
"""

from dicee import KGE
from core.reasoners import HermiT, NWR, SPARQLCWR, NC, Restriction, ValueRestriction
from util import compute_prediction, evaluate_results
import time
from dicee import KGE
import pandas as pd
import torch

pd.set_option("display.precision", 4)
pd.pandas.set_option('display.max_columns', None)

# (1) Load the model
pretrained_model = KGE("Experiments/2023-09-07 11-25-46.731312")
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
# (5) Get all roles.
relations = swr.query(
    "SELECT DISTINCT ?var WHERE { ?subject ?p <http://www.w3.org/2002/07/owl#NamedIndividual> .?subject ?var ?object .}")
# (5.1) Remove the type
relations.remove('<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>')
relations = list(relations)
# (6) Concept Creation: Create  atomic concepts, negations, unions ..
# Order Matters at testing time.
all_named_concepts = [NC(i) for i in all_named_concepts]
neg_named_concepts = [i.neg() for i in all_named_concepts]
# Create Unions and Intersections
unions = []
intersections = []
for i in all_named_concepts:
    for j in all_named_concepts:
        unions.append(i.union(j))
        intersections.append(i.intersection(j))
existential_res = []
universal_res = []
# Create Restrictions
for role_iri in relations:
    for filler in all_named_concepts:
        existential_res.append(Restriction(opt='∃', role=role_iri, filler=filler))
        universal_res.append(Restriction(opt='∀', role=role_iri, filler=filler))
value_at_least_restriction = []
value_at_most_restriction = []
for role_iri in relations:
    for filler in all_named_concepts:
        value_at_least_restriction.append(ValueRestriction(opt='≥', val=1, role=role_iri, filler=filler))
        value_at_most_restriction.append(ValueRestriction(opt='≤', val=3, role=role_iri, filler=filler))
# Initialize a Neural Reasoner
neural_reasoner = NWR(predictor=pretrained_model, gammas={'NC': 0.1, 'Exists': 0.7, 'Forall': 0.01, 'Value': 0.5},
                      all_named_individuals=all_named_individuals)

# Find suitable gamma thresholds for single hop prediction
#neural_reasoner.find_gammas(gammas=[0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.97, 1.00],
#                            concepts=[('NC', all_named_concepts)], true_func=hermit)
# Evaluate neural model with Fuseki triple store
for (name, i) in [('N_C', all_named_concepts),
                  ('neg N_C', neg_named_concepts),
                  ('Unions', unions),
                  ('Intersect', intersections),
                  ('Exists', existential_res),
                  ('Uni', universal_res),
                  ('AtLeast', value_at_least_restriction),
                  ('AtMost', value_at_most_restriction)
                  ]:
    print(f'{name} starts {len(i)}')
    df = evaluate_results(true_results=compute_prediction(i, predictor=hermit),
                          predictions=compute_prediction(i, predictor=neural_reasoner))
    print('######')
    print(name)
    if len(df)>0:
        # print(df)
        # print(df[['Similarity', 'ConceptSize', 'RTFuseki', 'RTnwr']].mean())
        print(df[['Similarity', 'ConceptSize', 'RTHermiT', 'RTnwr']].mean())
        # print(df[['Similarity', 'ConceptSize', 'RTHermiT', 'RTFuseki']].mean())
        print(df.to_latex(index=False, float_format="%.3f"))
    else:
        print('Size is 0.')