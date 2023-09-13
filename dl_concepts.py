from abc import ABC


class AbstractDLConcept(ABC):
    pass

    @property
    def sparql(self):
        try:
            return converter.as_query("?var", parser.parse_expression(self.str), False)
        except KeyError:
            # SPARQL query mapping
            print(self.str.strip())
            print(self.manchester_str)
            raise KeyError('Error at converting SPARQL query', self.str)


class Restriction(AbstractDLConcept):
    def __init__(self, opt: str = None, role: str = None, filler=None):
        super(Restriction, self)
        assert opt == '∃' or opt == '∀'
        assert role is not None
        self.opt = opt
        self.role_iri = role
        self.role = role.split('#')[-1][:-1]
        self.filler = filler
        if self.filler.length == 1:
            self.str = self.opt + ' ' + self.role + '.' + filler.str
        else:
            self.str = self.opt + ' ' + self.role + '.' + '(' + filler.str + ')'

        self.length = filler.length + 2

    @property
    def manchester_str(self):
        if self.opt == '∃':
            if self.filler.length > 1:
                return self.role + ' SOME ' + '(' + self.filler.manchester_str + ')'
            elif self.filler.length == 1:
                return self.role + ' SOME ' + self.filler.manchester_str
            else:
                raise KeyError(f'The length of the filler is invalid {self.filler.length}')
        elif self.opt == '∀':
            if self.filler.length > 1:
                return self.role + ' ONLY ' + '(' + self.filler.manchester_str + ')'
            elif self.filler.length == 1:
                return self.role + ' ONLY ' + self.filler.manchester_str
            else:
                raise KeyError(f'The length of the filler is invalid {self.filler.length}')
        else:
            raise KeyError(f'Invalid Opt. {self.opt}')

    def neg(self):
        if self.opt == '∃':
            # negation can be shifted past quantifiers.
            # ¬∃ r. C is converted into ∀ r. ¬C at the object creation
            # ¬∃ r. C \equiv ∀ r. ¬C
            return Restriction(opt='∀', role=self.role_iri, filler=self.filler.neg())
        elif self.opt == '∀':
            # ¬∀ r. C \equiv ¬∃ r. C
            return Restriction(opt='∃', role=self.role_iri, filler=self.filler.neg())
        else:
            raise KeyError(f'Wrong opt {self.opt}')

    def union(self, other):
        return DisjunctionDLConcept(concept_a=self, concept_b=other)

    def intersection(self, other):
        return ConjunctionDLConcept(concept_a=self, concept_b=other)


class ValueRestriction(AbstractDLConcept):
    def __init__(self, opt: str = None, val: int = None, role: str = None, filler=None):
        super(ValueRestriction, self)
        assert opt == '≥' or opt == '≤'
        assert role is not None
        assert isinstance(val, int)
        self.opt = opt
        self.val = val
        self.role_iri = role
        self.role = role.split('#')[-1][:-1]
        self.filler = filler
        self.str = self.opt + ' ' + f'{self.val} ' + self.role + '.' + filler.str
        # self.sparql = None

    @property
    def manchester_str(self):
        if self.opt == '≥':
            return self.role + ' MIN ' + f'{self.val} ' + self.filler.manchester_str
        elif self.opt == '≤':
            return self.role + ' MAX ' + f'{self.val} ' + self.filler.manchester_str


class ConjunctionDLConcept(AbstractDLConcept):
    def __init__(self, concept_a, concept_b):
        super(ConjunctionDLConcept, self)
        if concept_a.length == 1 and concept_b.length == 1:
            self.str = concept_a.str + " ⊓ " + concept_b.str
        elif concept_a.length == 1 and concept_b.length > 1:
            self.str = concept_a.str + " ⊓ " + "(" + concept_b.str + ")"
        elif concept_a.length > 1 and concept_b.length == 1:
            # Put the shorted one first.
            self.str = concept_b.str + " ⊓ " + "(" + concept_a.str + ")"
        elif concept_a.length > 1 and concept_b.length > 1:
            self.str = "(" + concept_a.str + " ⊓ " + concept_b.str + ")"
        else:
            raise KeyError()
        self.left = concept_a
        self.right = concept_b
        self.length = concept_a.length + concept_b.length + 1

    @property
    def manchester_str(self):
        left_part = self.left.manchester_str
        right_part = self.right.manchester_str
        if self.left.length > 1:
            left_part = "(" + left_part + ")"

        if self.right.length > 1:
            right_part = "(" + right_part + ")"
        return left_part + " AND " + right_part

    def neg(self):
        # \neg (C \sqcup D) \equiv \neg C \sqcap \neg D
        return DisjunctionDLConcept(concept_a=self.left.neg(), concept_b=self.right.neg())

    def union(self, other: AbstractDLConcept):
        return DisjunctionDLConcept(concept_a=self, concept_b=other)

    def intersection(self, other: AbstractDLConcept):
        return ConjunctionDLConcept(concept_a=self, concept_b=other)


class DisjunctionDLConcept(AbstractDLConcept):
    def __init__(self, concept_a, concept_b):
        super(DisjunctionDLConcept, self)
        if concept_a.length == 1 and concept_b.length == 1:
            self.str = concept_a.str + " ⊔ " + concept_b.str
        elif concept_a.length == 1 and concept_b.length > 1:
            self.str = concept_a.str + " ⊔ " + concept_b.str
        elif concept_b.length == 1 and concept_a.length > 1:
            self.str = concept_b.str + " ⊔ " + concept_a.str
        elif concept_b.length > 1 and concept_a.length > 1:
            self.str = "(" + concept_a.str + " ⊔ " + concept_b.str + ")"
        else:
            raise KeyError()

        self.left = concept_a
        self.right = concept_b
        self.length = concept_a.length + concept_b.length + 1

    @property
    def manchester_str(self):
        left_part = self.left.manchester_str
        right_part = self.right.manchester_str
        if self.left.length > 1:
            left_part = "(" + left_part + ")"

        if self.right.length > 1:
            right_part = "(" + right_part + ")"
        return left_part + " OR " + right_part

    def neg(self):
        # \neg (C \sqcap D) \equiv \neg C \sqcup \neg D
        return ConjunctionDLConcept(concept_a=self.left.neg(), concept_b=self.right.neg())

    def union(self, other: AbstractDLConcept):
        return DisjunctionDLConcept(concept_a=self, concept_b=other)

    def intersection(self, other: AbstractDLConcept):
        return ConjunctionDLConcept(concept_a=self, concept_b=other)


class NC(AbstractDLConcept):
    def __init__(self, iri: str):
        super(NC, self)
        assert isinstance(iri, str) and "#" in iri
        self.iri = iri
        assert self.iri[0] == '<' and self.iri[-1] == '>'
        self.str = self.iri.split('#')[-1][:-1]
        self.namespace=self.iri.split('#')[0][1:]+"#"
        self.length = 1

    @property
    def manchester_str(self):
        return self.str

    def neg(self):
        return NNC(iri=self.iri)

    def union(self, other: AbstractDLConcept):
        return DisjunctionDLConcept(self, other)

    def intersection(self, other: AbstractDLConcept):
        return ConjunctionDLConcept(self, other)


class NNC(AbstractDLConcept):
    def __init__(self, iri: str):
        super(NNC, self)
        assert iri[0] == '<' and iri[-1] == '>'
        self.neg_iri = iri
        self.str = "¬" + iri.split('#')[-1][:-1]
        self.length = 2
        self.namespace=iri.split('#')[0][1:]+"#"


    @property
    def manchester_str(self):
        return self.str.replace('¬', 'NOT ')

    def neg(self):
        return NC(self.neg_iri)

    def union(self, other: AbstractDLConcept):
        return DisjunctionDLConcept(self, other)

    def intersection(self, other: AbstractDLConcept):
        return ConjunctionDLConcept(self, other)
