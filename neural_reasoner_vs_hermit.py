from deeponto import init_jvm

try:
  MAX_JVM_MEMORY = "8g"
  init_jvm(MAX_JVM_MEMORY)
  
except Exception as e:
  print("cannot init jvm. ", e)

import rdflib.term
from dicee.executer import Execute
from dicee.config import Namespace
from dicee.knowledge_graph_embeddings import KGE
from rdflib.term import URIRef
from deeponto.onto import Ontology
import os
from core.quality_funcs import jaccard_similarity
from typing import Set
import torch
# https://krr-oxford.github.io/DeepOnto/ontology/
# See https://krr-oxford.github.io/DeepOnto/ontology/#ontology-reasoning
# @TODO: RL is it possible to fixing at the init so that we do not have to wait
# Please enter the maximum memory located to JVM [8g]:
# 8g maximum memory allocated to JVM.
# JVM started successfully.

path_ontology = "KGs/Family/Family.owl"
load_path = "Experiments/2023-09-07 11-25-46.731312"

def train_kge(path):
    # (1) Train Clifford Embeddings model with AllvsAll on Family dataset
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
    reports = Execute(args).start()
    # (2) Load the pretrained model
    return KGE(path=reports['path_experiment_folder'])
if load_path:
    pre_trained_kge = KGE(load_path)
else:
    pre_trained_kge = train_kge(path_ontology)

# mapping from string IRI of an individual or concept to the corresponding rdflib object.
# str of http://www.benchmark.org/family#married to  <class 'rdflib.term.URIRef'> of  http://www.benchmark.org/family#married
f = dict()
# k is rdflib
for k, v in pre_trained_kge.relation_to_idx.items():
    v: int
    k: rdflib.term.URIRef
    f[str(k)] = k
for k, v in pre_trained_kge.entity_to_idx.items():
    f[str(k)] = k



# get the ontology
onto = Ontology(path_ontology)
# A Threshold
gamma = 0.95

# Iterate over complex class expressions
# @TODO: Generate complex class expressions, e.g. Union, Intersection, Existential ∃ and Universal Quantifiers ∀


# try to create a union class expression
unions = []
for i in onto.owl_classes:
    owl_object_a = onto.get_owl_object_from_iri(i)
    for j in onto.owl_classes:
      owl_object_b = onto.get_owl_object_from_iri(j)
      tmp_unionClassExpression  = onto.owl_data_factory.getOWLObjectUnionOf(owl_object_a,owl_object_b)
      unions.append(tmp_unionClassExpression)

# testing
for i in unions:
  tmp = i.asDisjunctSet()
  print(tmp)
  
# try to create a intersection class expression
intersections = []
for i in onto.owl_classes:
    owl_object_a = onto.get_owl_object_from_iri(i)
    for j in onto.owl_classes:
      owl_object_b = onto.get_owl_object_from_iri(j)
      tmp_unionClassExpression  = onto.owl_data_factory.getOWLObjectIntersectionOf(owl_object_a,owl_object_b)
      intersections.append(tmp_unionClassExpression)

# testing
for i in unions:
  tmp = i.asConjunctSet()
  print(tmp)

existential_res = []
for p in onto.owl_object_properties:
  for i in onto.owl_classes:
    owl_object = onto.get_owl_object_from_iri(i)
    owl_property = onto.get_owl_object_from_iri(p)
    # owl_property = onto.owl_data_factory.getOWLObjectProperty(p)
    tmp_existential_class = onto.owl_data_factory.getOWLObjectSomeValuesFrom(owl_property,owl_object)
    existential_res.append(tmp_existential_class)

for i in existential_res:
  print(i.getClassExpressionType())



for i in onto.owl_classes:
    i: str  # IRI
    # (1) owlapi OBJECT owl_object: <java class 'uk.ac.manchester.cs.owl.owlapi.OWLClassImpl'>
    owl_object = onto.get_owl_object_from_iri(i)
    # print(owl_object)
    # unionClassExpression  = onto.owl_data_factory.getOWLObjectUnionOf(owl_object,owl_object)
    # (2) Return instanced/a set of individuals belonging owl_object: str(i)[1:-1] => removed brackets *< ... >
    y: Set[str]
    y = {str(i)[1:-1] for i in onto.reasoner.instances_of(owl_object)}

    # Neural Reasoning for Approximate Description Logic Concept Retrieval
    # (1) Assign scores for all entities  (?, type, Father),
    scores_for_all: torch.FloatTensor
    # scores_for_all[10] indicates the score of the 10th entity.
    scores_for_all = pre_trained_kge.predict(r=[f['http://www.w3.org/1999/02/22-rdf-syntax-ns#type']], t=[f[i]])
    # (2) Return all individuals that are assigned a triple score that is at least greater than gamma
    y_hat = {str(pre_trained_kge.idx_to_entity[index]) for index, flag in enumerate(scores_for_all >= gamma) if flag}
    # (3) Remove non entity predictions.
    print(f"DL Concept:{owl_object}\t Quality:{jaccard_similarity(y, y_hat)}")
