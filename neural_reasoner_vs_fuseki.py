""" Description Logic Concept Retrieval"""

from dicee.executer import Execute
from dicee.config import Namespace
from dicee.knowledge_graph_embeddings import KGE

from core.reasoners import NWR, SPARQLCWR, NC, Restriction, ValueRestriction
from util import compute_prediction, evaluate_results
import time
import pandas as pd
import torch

from rdflib.term import URIRef
import os
from core.quality_funcs import jaccard_similarity
from typing import Set

pd.set_option("display.precision", 4)
pd.pandas.set_option('display.max_columns', None)

# --------- (1) Load the model ---------

path_ontology = "KGs/Family/Family.owl"
load_path = "Experiments/2024-03-06 17-23-45.743681"


def train_kge(path):
    # --------- (1.1) Train Clifford Embeddings model with AllvsAll on Family dataset ---------

    args = Namespace()
    args.model = 'Keci'
    args.save_embeddings_as_csv = True
    args.path_dataset_folder = None
    args.scoring_technique = "AllvsAll"
    args.path_single_kg = path
    args.num_epochs = 100
    args.batch_size = 1024
    args.lr = 0.1
    args.embedding_dim = 512
    args.backend = "rdflib"
    reports = Execute(args).start()

    # --------- (1.2) Load the pretrained model ---------

    return KGE(path=reports['path_experiment_folder'])


if os.path.exists(load_path):
    pre_trained_kge = KGE(load_path)
else:
    pre_trained_kge = train_kge(path_ontology)


# --------- (2) Build a SPARQL connection ---------

swr = SPARQLCWR(url='http://localhost:3030/family/sparql', namespace="http://www.benchmark.org/family#", name='Fuseki')

# --------- (3) Get all named classes/concepts ---------

all_named_concepts = swr.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                               "SELECT DISTINCT ?var\n"
                               "WHERE {?var a owl:Class.}")

# --------- (4) Get all named individuals ---------

all_named_individuals = swr.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                                  "SELECT DISTINCT ?var\n"
                                  "WHERE {?var a owl:NamedIndividual.}")

# --------- (5) Get all roles ---------

relations = swr.query(
    "SELECT DISTINCT ?var WHERE { ?subject ?p <http://www.w3.org/2002/07/owl#NamedIndividual> .?subject ?var ?object .}")

# --------- (5.1) Remove the type ---------

relations.remove('<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>')
relations = list(relations)

# --------- (6) Concept Creation: Create  atomic concepts, negations, unions , etc. ---------

# --------- (6.1) Get all named concept and their negation. Order Matters at testing time ---------

all_named_concepts = [NC(i) for i in all_named_concepts]
neg_named_concepts = [i.neg() for i in all_named_concepts]

# --------- (6.2) Create Unions and Intersections ---------

unions = []
intersections = []
for i in all_named_concepts:
    for j in all_named_concepts:
        unions.append(i.union(j))
        intersections.append(i.intersection(j))
existential_res = []
universal_res = []

# --------- (6.3) Create Restrictions ---------

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

# # Initialize a Neural Reasoner
# neural_reasoner = NWR(predictor=pre_trained_kge, gammas={'NC': 0.1, 'Exists': 0.7, 'Forall': 0.01, 'Value': 0.5},
#                       all_named_individuals=all_named_individuals)
#
# # Find suitable gamma thresholds for single hop prediction
# neural_reasoner.find_gammas(gammas=[0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.97, 1.00],
#                             concepts=[('NC', all_named_concepts)], true_func=hermit)


# --------- Evaluate neural model (!?: evaluation code is commented) with Fuseki triple store ---------

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
    y = compute_prediction(i, predictor=swr)
    print(y)

    # df = evaluate_results(true_results=compute_prediction(i, predictor=swr),
    #                       predictions=compute_prediction(i, predictor=neural_reasoner))
    # print('######')
    # print(name)
    # if len(df) > 0:
    #     # print(df)
    #     # print(df[['Similarity', 'ConceptSize', 'RTFuseki', 'RTnwr']].mean())
    #     print(df[['Similarity', 'ConceptSize', 'RTHermiT', 'RTnwr']].mean())
    #     # print(df[['Similarity', 'ConceptSize', 'RTHermiT', 'RTFuseki']].mean())
    #     print(df.to_latex(index=False, float_format="%.3f"))
    # else:
    #     print('Size is 0.')
