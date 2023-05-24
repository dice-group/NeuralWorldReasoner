from abc import ABC

class AbstractDLConcept(ABC):
    pass


class Restriction(AbstractDLConcept):
    def __init__(self, opt: str = None, role: str = None, filler=None):
        super(Restriction, self)
        assert opt == '∃' or opt == '∀'
        assert role is not None
        self.opt = opt
        self.role_iri = role
        self.filler = filler
        self.str = self.opt + ' ' + role.split('#')[-1][:-1] + '.' + filler.str
        self.sparql = None


class ValueRestriction(AbstractDLConcept):
    def __init__(self, opt: str = None, val: int = None, role: str = None, filler=None):
        super(ValueRestriction, self)
        assert opt == '≥' or opt == '≤'
        assert role is not None
        assert isinstance(val, int)
        self.opt = opt
        self.val = val
        self.role_iri = role
        self.filler = filler
        self.str = self.opt + ' ' + f'{self.val} ' + role.split('#')[-1][:-1] + '.' + filler.str
        self.sparql = None


class ConjunctionDLConcept(AbstractDLConcept):
    def __init__(self, concept_a, concept_b):
        super(ConjunctionDLConcept, self)
        self.str = "(" + concept_a.str + " ⊓ " + concept_b.str + ")"
        self.left = concept_a
        self.right = concept_b
        self.sparql = None


class DisjunctionDLConcept(AbstractDLConcept):
    def __init__(self, concept_a, concept_b):
        super(DisjunctionDLConcept, self)
        self.str = "(" + concept_a.str + " ⊔ " + concept_b.str + ")"
        self.left = concept_a
        self.right = concept_b
        self.sparql = None


class NC(AbstractDLConcept):
    def __init__(self, iri):
        super(NC, self)
        self.iri = iri
        assert self.iri[0] == '<' and self.iri[-1] == '>'
        self.str = self.iri.split('#')[-1][:-1]
        self.sparql = None

    def neg(self):
        return NNC(iri=self.iri)

    def union(self, other: AbstractDLConcept):
        return ConjunctionDLConcept(self, other)

    def intersection(self, other: AbstractDLConcept):
        return DisjunctionDLConcept(self, other)


class NNC(AbstractDLConcept):
    def __init__(self, iri: str):
        super(NNC, self)
        assert iri[0] == '<' and iri[-1] == '>'
        self.neg_iri = iri
        self.str = "¬" + iri.split('#')[-1][:-1]
        self.sparql = None  # converter.as_query("?var", parser.parse_expression(self.str), False)

    def neg(self):
        return NC(self.neg_iri)

    def union(self, other: AbstractDLConcept):
        return ConjunctionDLConcept(self, other)

    def intersection(self, other: AbstractDLConcept):
        return DisjunctionDLConcept(self, other)
