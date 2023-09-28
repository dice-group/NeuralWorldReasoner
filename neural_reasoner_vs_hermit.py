from deeponto import init_jvm

try:
  MAX_JVM_MEMORY = "8g" # 8g maximum memory allocated to JVM by default. 
  init_jvm(MAX_JVM_MEMORY)
  
except Exception as e:
  print("cannot init jvm. ", e)


import rdflib.term
from dicee.executer import Execute
from dicee.config import Namespace
from dicee.knowledge_graph_embeddings import KGE
from rdflib.term import URIRef
from deeponto.onto import Ontology,OntologyReasoner
import os
from core.quality_funcs import jaccard_similarity
from typing import Set
import torch

from uk.ac.manchester.cs.owl.owlapi import OWLObjectUnionOfImpl,OWLObjectIntersectionOfImpl,OWLObjectSomeValuesFromImpl,OWLObjectAllValuesFromImpl # classes from java


# https://krr-oxford.github.io/DeepOnto/ontology/
# See https://krr-oxford.github.io/DeepOnto/ontology/#ontology-reasoning
# @TODO: RL is it possible to fixing at the init so that we do not have to wait (FIXED)
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

  

# initialize Hiermit resoner
onto_reasoner = OntologyReasoner(onto)
reasoner = onto_reasoner.owl_reasoner 




all_individuals = onto.owl_onto.getIndividualsInSignature() # get all individuals
owl_classes = [i for i in onto.owl_classes if i[i.index('#')+1:]!='Thing'] # get rid of 'Thing'
python_all_individuals = [str(i) for i in all_individuals] # convert rdflib of java to string of python


  

def _atomic_concept(concept: str,predictor) -> Set[str]:
  '''
  Using KGE predictor to predict individuals in a concept.
  Almost similar logic as the core/reasoner.py. 
  NC in gammas should be as low as possible, otherwise some of the results will be empty.
  (maybe my pre-trained model is not good enough)
  '''
  
  gammas={'NC': 0.0, 'Exists': 0.7, 'Forall': 0.01, 'Value': 0.5} 
  
  scores_for_all = predictor.predict(r=['<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'],
                                                t=[concept])
 
  raw_results = {predictor.idx_to_entity[index] for index, flag in
                       enumerate(scores_for_all >= gammas['NC']) if
                       flag}

  return {i for i in raw_results if i in python_all_individuals}


unions = []
for i in owl_classes:
    owl_object_a = onto.get_owl_object_from_iri(i)
    
    for j in owl_classes:

      owl_object_b = onto.get_owl_object_from_iri(j)
      tmp_unionClassExpression  = onto.owl_data_factory.getOWLObjectUnionOf(owl_object_a,owl_object_b)
      if tmp_unionClassExpression.asDisjunctSet().size() !=1:
        unions.append(tmp_unionClassExpression)



# for i in unions:
#   tmp = i.asDisjunctSet()
#   print(tmp)
  

# query individuals in union class with reasoner
# for union_class in unions:
#   individualsInUnion = reasoner.getInstances(union_class, False)
  # print(individualsInUnion)
  # print("***************************")



# try to create a intersection class expression
intersections = []
for i in owl_classes:
    owl_object_a = onto.get_owl_object_from_iri(i)
    for j in owl_classes:
      owl_object_b = onto.get_owl_object_from_iri(j)
      tmp_intersectionClassExpression  = onto.owl_data_factory.getOWLObjectIntersectionOf(owl_object_a,owl_object_b)
      if tmp_intersectionClassExpression.asConjunctSet().size() !=1:
        intersections.append(tmp_intersectionClassExpression)

# testing
# for i in intersections:
#   tmp = i.asConjunctSet()
#   print(tmp)



# query individuals in union class with reasoner
# for intersectiion_class in intersections:
#   individualsInIntersection = reasoner.getInstances(intersectiion_class, False)
#   print(individualsInIntersection)
#   print("***************************")


existential_res = []
for p in onto.owl_object_properties:
  owl_property = onto.get_owl_object_from_iri(p)
  for i in owl_classes:
    owl_object = onto.get_owl_object_from_iri(i)
    tmp_existential_class = onto.owl_data_factory.getOWLObjectSomeValuesFrom(owl_property,owl_object)
    existential_res.append(tmp_existential_class)


# for i in existential_res:
#   print(i.getClassExpressionType())


# for i in existential_res:
#   tmp = i.asConjunctSet()
#   print(tmp)


# for existential_class in existential_res:
#   individualsInExistential = reasoner.getInstances(existential_class, False)
#   print(individualsInExistential)
#   print("***************************")
  


universal_res = []
for p in onto.owl_object_properties:
  owl_property = onto.get_owl_object_from_iri(p)
  for i in owl_classes:
    owl_object = onto.get_owl_object_from_iri(i)
    tmp_universal_class = onto.owl_data_factory.getOWLObjectAllValuesFrom(owl_property,owl_object)
    universal_res.append(tmp_universal_class)





def comparator(class_expression,ignore_empty_concept = True):
  
  for i in class_expression:
    
    # tmp = i.asConjunctSet()
    # print(tmp)
    # isConsistent = reasoner.isConsistent() # check if the ontology is consistent
    # print(isConsistent)
    
    
    individuals_in_class_exp = reasoner.getInstances(i, False)
    class_exp_str = ''
    y=[]
    for j in individuals_in_class_exp:
      individual = j.getRepresentativeElement().toString()
      y.append(individual)
      
    tmp = []
    if isinstance(i, OWLObjectUnionOfImpl):
      tmp = i.asDisjunctSet()
      class_exp_str = 'union'
    elif isinstance(i, OWLObjectIntersectionOfImpl):
      tmp = i.asConjunctSet()
      class_exp_str = 'intersection'
    elif isinstance(i,OWLObjectSomeValuesFromImpl):
      tmp = i.asConjunctSet()
      class_exp_str = 'exist'
    elif isinstance(i,OWLObjectAllValuesFromImpl):
      tmp = i.asConjunctSet()
      class_exp_str = 'universal'

    concepts = []
    for concept in tmp:
      concepts.append(concept)


    if isinstance(i,OWLObjectSomeValuesFromImpl) or isinstance(i,OWLObjectAllValuesFromImpl):
      left = '<'+str(concepts[0].getProperty().getIRI().toString())+'>'
      right = '<'+str(concepts[0].getFiller().getIRI().toString())+'>'
    else:
      left = '<'+str(concepts[0].getIRI().toString())+'>'
      right = '<'+str(concepts[1].getIRI().toString())+'>'
    
    
    
    if isinstance(i, OWLObjectUnionOfImpl):
      pre = _atomic_concept(left,pre_trained_kge).union(_atomic_concept(right,pre_trained_kge))
    elif isinstance(i, OWLObjectIntersectionOfImpl):
      pre = _atomic_concept(left,pre_trained_kge).intersection(_atomic_concept(right,pre_trained_kge))
    elif isinstance(i,OWLObjectSomeValuesFromImpl):
      pre = existential_restriction(right,left,pre_trained_kge)
    elif isinstance(i,OWLObjectAllValuesFromImpl):
      pre = universal_restriction(right,left,pre_trained_kge)


    # compute similarity
    if len(set(y)) ==0 and ignore_empty_concept:
      continue
    else:
      print(f"DL Concept:{left[left.find('#')+1:-1]} {class_exp_str} {right[right.find('#')+1:-1]}\t Quality:{jaccard_similarity(set(y), pre)}")



def existential_restriction(filler_concept,role,predictor,filler_individuals=None):
  '''
  Almost similar logic as the core/reasoner.py
  '''
  
  gammas={'NC': 0.1, 'Exists': 0.7, 'Forall': 0.01, 'Value': 0.5}
  
  if filler_concept:
    filler_individuals = _atomic_concept(filler_concept,predictor)
  elif filler_individuals is not None:
    filler_individuals = filler_individuals
  else:
    filler_individuals = python_all_individuals

  results = set()
  
  # (2) For each filler individual
  for i in filler_individuals:
      # (2.1) Assign scores for all subjects.
      scores_for_all = predictor.predict(r=[role], t=[i])
      ids = (scores_for_all >= gammas['Exists']).nonzero(as_tuple=True)[0].tolist()
      if len(ids) >= 1:
          results.update(set(ids))
      else:
          continue
  return {predictor.idx_to_entity[i] for i in results}


def universal_restriction(filler_concept,role,predictor):
    
    '''
    Resoner of Hermit return emppty set for universal restriction.
    Not sure why. NEED TO BE FIXED.  
    '''
    
    # individuals that not fulfill existential restriction
    negate_concept = set(python_all_individuals) - existential_restriction(filler_concept, role,predictor) 
    return set(python_all_individuals).difference(negate_concept) 


def negate_concept(concept, predictor):
   return python_all_individuals - predictor.predict(concept)
 
comparator(unions)
comparator(intersections)
comparator(existential_res)



# comparator(universal_res) # not work for now