from reasoners import HermiT
from dl_concepts import *


def retrieve(concept):
    return reasoner.retrieve(concept)

reasoner = HermiT(url='http://localhost:8080/hermit')

def commutativity_checking(C, D):
    # commutativity: (C ⊓ D) = (D ⊓ C)
    assert retrieve(C.intersection(D)) == retrieve(D.intersection(C))

def associativity_checking(C, D, E):
    # associativity:(C ⊓ D) ⊓ E = C ⊓ (D ⊓ E)
    assert retrieve(C.intersection(D).intersection(E)) == retrieve(C.intersection(D.intersection(E)))

def idempotency_checking_with_sparql(C):
    # idempotency (C ⊓ C) = C as well as  (C ⊔ C) = C
    assert retrieve(C.intersection(C)) == retrieve(C)
    assert retrieve(C.union(C)) == retrieve(C)

def de_morgan_laws(C, D, E):
    # (C ⊔ D) ⊓ E = (C ⊓ E) ⊔ (D ⊓ E)
    result1 = retrieve(C.union(D).intersection(E))
    result2 = retrieve(C.intersection(E)) | retrieve(D.intersection(E))
    assert result1 == result2
    # ¬(C ⊔ D) \equiv ¬C ⊓ ¬D .
    result1 = retrieve(C.union(D).neg())
    assert result1 == retrieve(C.neg().union(D.neg()))


Brother = NC("<http://www.benchmark.org/family#Brother>")
Female = NC("<http://www.benchmark.org/family#Female>")
Sister = NC("<http://www.benchmark.org/family#Sister>")
Mother = NC("<http://www.benchmark.org/family#Mother>")
Father = NC("<http://www.benchmark.org/family#Father>")


forall_hasSibling_Sister = Restriction(opt='∀', role="<http://www.benchmark.org/family#hasSibling>",
                                       filler=Female)
exists_hasSibling_Sister = Restriction(opt='∃', role="<http://www.benchmark.org/family#hasSibling>",
                                       filler=Female)


concepts = [Father, Brother, Female, Sister, Mother, forall_hasSibling_Sister, exists_hasSibling_Sister]
long_concepts = set()

for i in concepts:
    for j in concepts:
        long_concepts.add(i.union(j)) # i ⊔ j
        long_concepts.add(i.intersection(j)) # i ⊓ j
        
print(f'Iterating over {len(long_concepts)} concepts')



"""
reasoner(Hiermit) retrieve the result in respect to each concept in the list
"""

for t, i in enumerate(long_concepts):
    print(f"{t}.th concept: {i.manchester_str}")
    idempotency_checking_with_sparql(i)
    for j in concepts:
        commutativity_checking(i, j)
        associativity_checking(i, j, i.union(j))
        associativity_checking(i.intersection(j), j, i)

        de_morgan_laws(i, j, i)
        de_morgan_laws(i, j, i.union(j))
        de_morgan_laws(i, j.intersection(i), i)



"""
(nrw) renzhong@litcqd:~/jena/NeuralWorldReasoner$ python syntax_analysis.py 
Iterating over 98 concepts
0.th concept: Female OR Mother
1.th concept: Female AND Mother
2.th concept: Female OR (hasSibling ONLY Female)
3.th concept: Female AND (hasSibling ONLY Female)
4.th concept: Female OR (hasSibling SOME Female)
5.th concept: Female AND (hasSibling SOME Female)
6.th concept: Sister OR Father
7.th concept: Sister AND Father
8.th concept: Sister OR Brother
9.th concept: Sister AND Brother
10.th concept: Sister OR Female
11.th concept: Sister AND Female
12.th concept: Sister OR Sister
13.th concept: Sister AND Sister
14.th concept: Sister OR Mother
15.th concept: Sister AND Mother
16.th concept: Sister OR (hasSibling ONLY Female)
17.th concept: Sister AND (hasSibling ONLY Female)
18.th concept: Sister OR (hasSibling SOME Female)
19.th concept: Sister AND (hasSibling SOME Female)
20.th concept: Mother OR Father
21.th concept: Mother AND Father
22.th concept: Mother OR Brother
23.th concept: Mother AND Brother
24.th concept: Mother OR Female
25.th concept: Mother AND Female
26.th concept: Mother OR Sister
27.th concept: Mother AND Sister
28.th concept: Mother OR Mother
29.th concept: Mother AND Mother
30.th concept: Mother OR (hasSibling ONLY Female)
31.th concept: Mother AND (hasSibling ONLY Female)
32.th concept: Mother OR (hasSibling SOME Female)
33.th concept: Mother AND (hasSibling SOME Female)
34.th concept: (hasSibling ONLY Female) OR Father
35.th concept: (hasSibling ONLY Female) AND Father
36.th concept: (hasSibling ONLY Female) OR Brother
37.th concept: (hasSibling ONLY Female) AND Brother
38.th concept: (hasSibling ONLY Female) OR Female

"""