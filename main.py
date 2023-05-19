from reasoners import NWR, CWR, SPARQLCWR
from util import jaccard_similarity
import time
from dicee import KGE
import pandas as pd
import torch

pd.set_option("display.precision", 3)
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

swr = SPARQLCWR(url='http://localhost:3030/family/sparql', name='Fuseki')
neural_kb = NWR(predictor=pretrained_model, gamma=0.25, all_named_individuals=all_named_individuals)
cwr = CWR(database=kg, all_named_individuals=all_named_individuals)


def compute_similarity(concepts: set[str], retriever: object, pred_retriever: object, f=jaccard_similarity,type_="atomic_concept"):
    """

    :param type_:
    :param pred_retriever:
    :param retriever:
    :param concepts: a set of concepts
    :param f: a similarity function
    :return: Float
    """
    results = []
    avg_sims = 0
    rt_retriever = 0
    rt_pred_retriever = 0
    for c in concepts:
        start_time = time.time()
        y = getattr(retriever, type_)(concept=c)
        rt_retriever += time.time() - start_time

        start_time = time.time()
        yhat = getattr(pred_retriever, type_)(concept=c)
        rt_pred_retriever += time.time() - start_time

        sim = f(y=y, yhat=yhat)
        #print(
        #    f"Retrieval Task:{i}\tSim:{sim}\t|y|={len(y)}\t|yhat|={len(yhat)}\tRT {retriever.name}:{rt_retriever:.3f}\t RT {pred_retriever.name}:{rt_pred_retriever:.3f}")


        plain_concept=c.split('#')[-1][:-1]

        if type_=='negated_atomic_concept':
            plain_concept="¬"+plain_concept
        results.append({'Concept': plain_concept, 'ConceptSize': len(y), 'Jaccard': sim,
                        f'{retriever.name}': rt_retriever, f'{pred_retriever.name}': rt_pred_retriever})
        avg_sims += sim
    avg_sims /= len(concepts)

    df=pd.DataFrame(results)
    return df
    #print(df.to_latex(index=False,float_format="%.3f"))
    ## print(df['Jacc_Sim'].mean())

assert compute_similarity(all_named_concepts, type_="atomic_concept", retriever=swr, pred_retriever=cwr)['Jaccard'].mean()==compute_similarity(all_named_concepts, type_="negated_atomic_concept", retriever=swr, pred_retriever=cwr)['Jaccard'].mean()==1.0

compute_similarity(all_named_concepts, type_="atomic_concept", retriever=swr, pred_retriever=neural_kb)
compute_similarity(all_named_concepts, type_="negated_atomic_concept", retriever=swr, pred_retriever=neural_kb)
exit(1)
print(jaccard_similarity(y=cwr.universal_restriction(role='<http://www.benchmark.org/family#married>',
                                                     filler_concept='<http://www.benchmark.org/family#Female>'),
                         yhat=nwr.universal_restriction(role='<http://www.benchmark.org/family#married>',
                                                        filler_concept='<http://www.benchmark.org/family#Female>')))

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
