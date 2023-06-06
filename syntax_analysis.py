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
        long_concepts.add(i.union(j))
        long_concepts.add(i.intersection(j))
print(f'Iterating over {len(long_concepts)} concepts')
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
