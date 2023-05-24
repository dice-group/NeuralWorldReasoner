from reasoners import NWR, CWR, SPARQLCWR, NC, AbstractReasoner, AbstractDLConcept, Restriction, ValueRestriction
from util import jaccard_similarity, compute_prediction, evaluate_results
import time
from dicee import KGE
import pandas as pd
import torch

pd.set_option("display.precision", 4)
pd.pandas.set_option('display.max_columns', None)

# (1) Load the model
pretrained_model = KGE("Experiments/2023-05-24 11:53:06.006435")

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

relations = swr.query(
    "SELECT DISTINCT ?var WHERE { ?subject ?p <http://www.w3.org/2002/07/owl#NamedIndividual> .?subject ?var ?object .}")
relations.remove('<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>')
relations = list(relations)
neural_kb = NWR(predictor=pretrained_model, gammas={'NC': 0.1, 'Forall': 0.1, 'Exists': 0.2, 'Value': 0.2},
                all_named_individuals=all_named_individuals)
cwr = CWR(database=kg, all_named_individuals=all_named_individuals)

# Create Negated Atomic Concepts.
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

# Find suitable gammas
#neural_kb.find_gammas(
#    gammas=[0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95],
#    concepts=[('NC', all_named_concepts), ('Exists', existential_res), ('Forall', universal_res),
#              ('Value', value_at_least_restriction)])

for (name, i) in [('N_C', all_named_concepts),
                  ('neg N_C', neg_named_concepts),
                  ('Unions', unions),
                  ('Intersect', intersections),
                  ('Exists', existential_res),
                  ('Uni', universal_res),
                  ('AtLeast', value_at_least_restriction),
                  ('AtMost', value_at_most_restriction)
                  ]:
    df = evaluate_results(true_results=compute_prediction(i, predictor=swr),
                          predictions=compute_prediction(i, predictor=neural_kb))
    print('######')
    print(name)
    # print(df)
    # print(df.to_latex(index=False,float_format="%.3f"))
    print(df[['Similarity', 'ConceptSize', 'RTFuseki', 'RTnwr']].mean())

exit(1)

# Compare triple store results via SPARQL
assert evaluate_results(true_results=compute_prediction(universal_res, predictor=swr),
                        predictions=compute_prediction(universal_res, predictor=cwr))['Similarity'].mean() == 1.0
assert evaluate_results(true_results=compute_prediction(existential_res, predictor=cwr),
                        predictions=compute_prediction(existential_res, predictor=swr))['Similarity'].mean() == 1.0
assert evaluate_results(true_results=compute_prediction(all_named_concepts, predictor=cwr),
                        predictions=compute_prediction(all_named_concepts, predictor=swr))['Similarity'].mean() == 1.0
assert evaluate_results(true_results=compute_prediction(neg_named_concepts, predictor=cwr),
                        predictions=compute_prediction(neg_named_concepts, predictor=swr))['Similarity'].mean() == 1.0
assert evaluate_results(true_results=compute_prediction(intersections, predictor=cwr),
                        predictions=compute_prediction(intersections, predictor=swr))['Similarity'].mean() == 1.0
assert evaluate_results(true_results=compute_prediction(unions, predictor=cwr),
                        predictions=compute_prediction(unions, predictor=swr))['Similarity'].mean() == 1.0
