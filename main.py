from reasoners import NWR, CWR, SPARQLCWR
from util import jaccard

from dicee import KGE
import pandas as pd
import torch
from typing import Set



# (1) Load the model
pretrained_model = KGE('Experiments/2023-05-03 12:14:26.873840')
lp = {"Aunt": {
    "positive_examples": [
        "http://www.benchmark.org/family#F2F14",
        "http://www.benchmark.org/family#F2F12",
        "http://www.benchmark.org/family#F2F19",
        "http://www.benchmark.org/family#F2F26",
        "http://www.benchmark.org/family#F2F28",
        "http://www.benchmark.org/family#F2F36",
        "http://www.benchmark.org/family#F3F52",
        "http://www.benchmark.org/family#F3F53",
        "http://www.benchmark.org/family#F5F62"
        , "http://www.benchmark.org/family#F6F72"
        , "http://www.benchmark.org/family#F6F79"
        , "http://www.benchmark.org/family#F6F77"
        , "http://www.benchmark.org/family#F6F86"
        , "http://www.benchmark.org/family#F6F91"
        , "http://www.benchmark.org/family#F6F84"
        , "http://www.benchmark.org/family#F6F96"
        , "http://www.benchmark.org/family#F6F101"
        , "http://www.benchmark.org/family#F6F93"
        , "http://www.benchmark.org/family#F7F114"
        , "http://www.benchmark.org/family#F7F106"
        , "http://www.benchmark.org/family#F7F116"
        , "http://www.benchmark.org/family#F7F119"
        , "http://www.benchmark.org/family#F7F126"
        , "http://www.benchmark.org/family#F7F121"
        , "http://www.benchmark.org/family#F9F148"
        , "http://www.benchmark.org/family#F9F150"
        , "http://www.benchmark.org/family#F9F143"
        , "http://www.benchmark.org/family#F9F152"
        , "http://www.benchmark.org/family#F9F154"
        , "http://www.benchmark.org/family#F9F141"
        , "http://www.benchmark.org/family#F9F160"
        , "http://www.benchmark.org/family#F9F163"
        , "http://www.benchmark.org/family#F9F158"
        , "http://www.benchmark.org/family#F9F168"
        , "http://www.benchmark.org/family#F10F174"
        , "http://www.benchmark.org/family#F10F179"
        , "http://www.benchmark.org/family#F10F181"
        , "http://www.benchmark.org/family#F10F192"
        , "http://www.benchmark.org/family#F10F193"
        , "http://www.benchmark.org/family#F10F186"
        , "http://www.benchmark.org/family#F10F195"
    ],
    "negative_examples": ["http://www.benchmark.org/family#F6M99"
        , "http://www.benchmark.org/family#F10F200"
        , "http://www.benchmark.org/family#F9F156"
        , "http://www.benchmark.org/family#F6M69"
        , "http://www.benchmark.org/family#F2F15"
        , "http://www.benchmark.org/family#F6M100"
        , "http://www.benchmark.org/family#F8F133"
        , "http://www.benchmark.org/family#F3F48"
        , "http://www.benchmark.org/family#F2F30"
        , "http://www.benchmark.org/family#F4F55"
        , "http://www.benchmark.org/family#F6F74"
        , "http://www.benchmark.org/family#F10M199"
        , "http://www.benchmark.org/family#F7M104"
        , "http://www.benchmark.org/family#F9M146"
        , "http://www.benchmark.org/family#F6M71"
        , "http://www.benchmark.org/family#F2F22"
        , "http://www.benchmark.org/family#F2M13"
        , "http://www.benchmark.org/family#F9F169"
        , "http://www.benchmark.org/family#F5F65"
        , "http://www.benchmark.org/family#F6M81"
        , "http://www.benchmark.org/family#F7M131"
        , "http://www.benchmark.org/family#F7F129"
        , "http://www.benchmark.org/family#F7M107"
        , "http://www.benchmark.org/family#F10F189"
        , "http://www.benchmark.org/family#F8F135"
        , "http://www.benchmark.org/family#F8M136"
        , "http://www.benchmark.org/family#F10M188"
        , "http://www.benchmark.org/family#F9F164"
        , "http://www.benchmark.org/family#F7F118"
        , "http://www.benchmark.org/family#F2F10"
        , "http://www.benchmark.org/family#F6F97"
        , "http://www.benchmark.org/family#F7F111"
        , "http://www.benchmark.org/family#F9M151"
        , "http://www.benchmark.org/family#F4M59"
        , "http://www.benchmark.org/family#F2M37"
        , "http://www.benchmark.org/family#F1M1"
        , "http://www.benchmark.org/family#F9M142"
        , "http://www.benchmark.org/family#F4M57"
        , "http://www.benchmark.org/family#F9M170"
        , "http://www.benchmark.org/family#F5M66"
        , "http://www.benchmark.org/family#F9F145"
                          ]
}}

pos = lp['Aunt']['positive_examples']
neg = lp['Aunt']['negative_examples']
entities = list(pretrained_model.entity_to_idx.keys())

kg = pd.read_csv('KGs/Family/train.txt', sep="\s+", header=None, usecols=[0, 1, 2],
                 names=['subject', 'relation', 'object'], dtype=str)

all_named_indv = set(kg[(kg['relation'] == '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') & (
        kg['object'] == '<http://www.w3.org/2002/07/owl#NamedIndividual>')]['subject'].tolist())


nwr = NWR(predictor=pretrained_model, gamma=0.7)
cwr = CWR(database=kg)
# SPARQLCWR()


print(jaccard(y=cwr.universal_restriction(role='<http://www.benchmark.org/family#married>',
                                            filler_concept='<http://www.benchmark.org/family#Female>'),
              yhat=nwr.universal_restriction(role='<http://www.benchmark.org/family#married>',
                                               filler_concept='<http://www.benchmark.org/family#Female>')))


print(jaccard(y=cwr.existential_restriction(role='<http://www.benchmark.org/family#married>',
                                            filler_concept='<http://www.benchmark.org/family#Female>'),
              yhat=nwr.existential_restriction(role='<http://www.benchmark.org/family#married>',
                                               filler_concept='<http://www.benchmark.org/family#Female>')))

print('Jaccard(CWR(Female ⊓ Sister),NWR(Female ⊓ Sister)):',
      jaccard(y=cwr.conjunction('<http://www.benchmark.org/family#Female>', '<http://www.benchmark.org/family#Sister>'),
              yhat=nwr.conjunction('<http://www.benchmark.org/family#Female>',
                                   '<http://www.benchmark.org/family#Sister>')))

print('Jaccard(CWR(Female ⊔ Sister),NWR(Female ⊔ Sister)):',
      jaccard(y=cwr.disjunction('<http://www.benchmark.org/family#Female>', '<http://www.benchmark.org/family#Sister>'),
              yhat=nwr.disjunction('<http://www.benchmark.org/family#Female>',
                                   '<http://www.benchmark.org/family#Sister>')))
