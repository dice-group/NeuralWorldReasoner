from reasoners import NWR, CWR, SPARQLCWR, NC, AbstractReasoner, AbstractDLConcept, Restriction, ValueRestriction
from dicee import KGE
import json

from util import compute_prediction, evaluate_results, f1_score
import time
import pandas as pd
import torch
from dl_concepts import *
from owlapy.parser import DLSyntaxParser
from owlapy.owl2sparql.converter import Owl2SparqlConverter

parser = DLSyntaxParser("http://www.benchmark.org/family#")
converter = Owl2SparqlConverter()


x=Restriction(opt='∃', role="<http://www.benchmark.org/family#hasSibling>", filler=NC("<http://www.benchmark.org/family#Sister>"))

#print(x.str)
sparql_query = converter.as_query("?var", parser.parse_expression(x.str), False)
#print(sparql_query)

x=Restriction(opt='∀', role="<http://www.benchmark.org/family#hasSibling>", filler=NC("<http://www.benchmark.org/family#Sister>").neg())

print(x.str)

sparql_query = converter.as_query("?var", parser.parse_expression(x.str), False)

print(sparql_query)
exit(1)

print('#####')
x=Restriction(opt='∀', role="<http://www.benchmark.org/family#hasSibling>", filler=NC("<http://www.benchmark.org/family#Sister>").neg())


print(x.str)
sparql_query = converter.as_query("?var", parser.parse_expression(x.str), False)
print(sparql_query)



exit(1)




# (2) Build a SPARQL connection
swr = SPARQLCWR(url='http://localhost:3030/family/sparql', name='Fuseki')


# (4) Get all named individuals
all_named_individuals = swr.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                                  "SELECT DISTINCT ?var\n"
                                  "WHERE {?var a owl:NamedIndividual.}")

# Pg. 30 https://www.aifb.kit.edu/images/1/19/DL-Intro.pdf
# What about C AND D and (NOT (NOT C OR NOT D))?


exists_hassibling_sister=Restriction(opt='∃', role="<http://www.benchmark.org/family#hasSibling>", filler=NC("<http://www.benchmark.org/family#Sister>"))
#print(f"{exists_hassibling_sister.str}")
# \neg \exists r. C
y=all_named_individuals.difference(swr.predict(exists_hassibling_sister))
#print(exists_hassibling_sister.sparql)

#print(y)
#print(len(y))

forall_hassibling_neg_sister=Restriction(opt='∀', role="<http://www.benchmark.org/family#hasSibling>", filler=NC("<http://www.benchmark.org/family#Sister>").neg())
print(forall_hassibling_neg_sister.str)
# \forall r. \neg C
yhat=swr.predict(forall_hassibling_neg_sister)
#print(yhat)

# ¬∃ hasSibling.Sister
# ∀ hasSibling.¬Sister
# <http://www.benchmark.org/family#F6M95> does only occur in the answer set of ¬∃ hasSibling.Sister.

# Observation:<http://www.benchmark.org/family#F6M95> does not have any hasSibling hence
# the computation of ¬∃ hasSibling.Sister is correct.

# ∀ hasSibling.bottom

# <http://www.benchmark.org/family#F6M95> =>

# A implies B
# A=\forall b(a,b) \in r^I
# A TRUE

# (∀r.C)  = {a | ∀ b. ((a, b) ∈ r =>  b ∈ C)}

# A= (a, b) ∈ r
# B= b ∈ C


# Given a=<http://www.benchmark.org/family#F6M95>
# A becomes FALSE
# Regardless of B TRUE or False
exit(1)




forall_hasSibling_Sister=Restriction(opt='∀', role="<http://www.benchmark.org/family#hasSibling>", filler=NC("<http://www.benchmark.org/family#Sister>"))
print(forall_hasSibling_Sister.str)
# Retrieve the individuals of ∀ hasSibling.¬Sister
y=swr.predict(forall_hasSibling_Sister)
# Negate it or not \domain^I -  (∀ hassibling \neg Sister)^I

assert y==yhat
exit(1)
yhat=all_named_individuals-yhat


# Create a  concept => ∀ hassibling \neg Sister
forall_hasSibling_not_Sister=Restriction(opt='∀', role="<http://www.benchmark.org/family#hasSibling>", filler=NC("<http://www.benchmark.org/family#Sister>").neg())
print(forall_hasSibling_not_Sister.str)
# Retrieve the individuals of ∀ hasSibling.¬Sister
yhat=swr.predict(forall_hasSibling_not_Sister)
# Negate it or not \domain^I -  (∀ hassibling \neg Sister)^I
yhat=all_named_individuals-yhat
# yhat => Retrieval (\neg)
print(len(y))
print(len(yhat))
print('####')
print(y.difference(yhat))

print('####')

print(yhat.difference(y))

print(y==yhat)


exit(1)
path_of_json_learning_problems = 'LPs/Family/lp_dl_learner.json'
with open(path_of_json_learning_problems, 'r') as f:
    lp = json.load(f)['problems']
pos = {'<' + i + '>' for i in lp['Aunt']['positive_examples']}
neg = {'<' + i + '>' for i in lp['Aunt']['negative_examples']}








class CL:
    def __init__(self, reasoner):
        self.reasoner = reasoner
        self.search_tree = []

    def get_most_promissing(self):
        self.search_tree.sort(key=lambda x: x[1])
        concept, _ = self.search_tree[0]
        return concept

    def refine(self, x):
        if x == 'Top':
            swr.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                      "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
                      "SELECT ?var\n"
                      "WHERE { ?var a owl:Class ."
                      "FILTER NOT EXISTS{ ?var rdfs: subClassOf ?sup. FILTER(?sup != owl: Thing)}}")

    def fit(self, set_pos, set_neg):
        self.search_tree.append(('Top', f1_score(yhat=swr.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                                                                "SELECT DISTINCT ?var\n"
                                                                "WHERE {?var a owl:Thing.}"), pos=set_pos,
                                                 neg=set_neg)))
        for i in range(10):
            most_promising = self.get_most_promissing()
            for concept in self.refine(most_promising):
                score = f1_score(self.reasoner.retrieve(concept), set_pos, set_neg)
                if score > 0.0:
                    self.search_tree.append((concept.str, score))

        prediction = self.get_most_promissing()
        f1 = f1_score(self.reasoner.retrieve(prediction), set_pos, set_neg)

        return prediction, f1


x = CL(reasoner=swr).fit(pos, neg)
print(x)

exit(1)
# (3) Get all owlclasses
all_named_concepts = swr.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                               "SELECT DISTINCT ?var\n"
                               "WHERE {?var a owl:Class.}")
# (4) Get all named individuals
all_named_individuals = swr.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                                  "SELECT DISTINCT ?var\n"
                                  "WHERE {?var a owl:NamedIndividual.}")
# (5) Get all roles
relations = swr.query(
    "SELECT DISTINCT ?var WHERE { ?subject ?p <http://www.w3.org/2002/07/owl#NamedIndividual> .?subject ?var ?object .}")
relations.remove('<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>')
relations = list(relations)

# (6) Create concepts.
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

neural_kb = NWR(predictor=pretrained_model, gammas={'NC': 0.1, 'Exists': 0.7, 'Forall': 0.95, 'Value': 0.5},
                all_named_individuals=all_named_individuals)

# neural_kb.find_gammas(
#    gammas=[0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.97, 1.00],
#    concepts=[('NC', all_named_concepts), ('Exists', existential_res), ('Forall', universal_res),
#              ('Value', value_at_least_restriction)], true_func=swr)

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
    # print(df.to_latex(index=False, float_format="%.3f"))
    print(df[['Similarity', 'ConceptSize', 'RTFuseki', 'RTnwr']].mean())

exit(1)
# (1) Load the model.
pretrained_model = KGE("Experiments/2023-05-16 10:51:31.694192")
# (2)
for i in pos:
    # (2) Predict types of positives.
    scores_for_all = pretrained_model.predict(head_entities=[i],
                                              relations=['<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>']).flatten()
    # (2) Iterative (1) and return entities whose predicted score satisfies the condition.
    raw_results = {pretrained_model.idx_to_entity[index] for index, flag in enumerate(scores_for_all >= 0.8) if
                   flag}
    result = {i for i in raw_results if 'http://www.benchmark.org/family#' in i}
    print(result)

"""
SELECT DISTINCT ?var ?cnt_1 ?cnt_2 WHERE { 
?var <http://www.benchmark.org/family#hasSibling> ?s_1 . 
{ SELECT ?var ( COUNT( ?s_2 ) AS ?cnt_1 ) WHERE { 
?var <http://www.benchmark.org/family#hasSibling> ?s_2 . 
?s_2 ?p ?o .  
FILTER NOT EXISTS { 
?s_2 a <http://www.benchmark.org/family#Sister> . 
 }
 } GROUP BY ?var }
{ SELECT ?var ( COUNT( ?s_3 ) AS ?cnt_2 ) WHERE { 
?var <http://www.benchmark.org/family#hasSibling> ?s_3 . 
 } GROUP BY ?var } }
"""