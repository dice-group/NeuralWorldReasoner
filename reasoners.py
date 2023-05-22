from abc import ABC, abstractmethod
from typing import Set
import requests
from owlapy.parser import DLSyntaxParser
from owlapy.owl2sparql.converter import Owl2SparqlConverter

parser = DLSyntaxParser("http://www.benchmark.org/family#")
converter = Owl2SparqlConverter()


# print(converter.as_query("?var", parser.parse_expression('≥ 2 hasChild.Mother'), False))

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


class AbstractReasoner(ABC):
    def predict(self, concept) -> Set[str]:
        if isinstance(concept, NC):
            return self.atomic_concept(concept)
        elif isinstance(concept, NNC):
            return self.negated_atomic_concept(concept)
        elif isinstance(concept, ConjunctionDLConcept):
            return self.conjunction(concept)
        elif isinstance(concept, DisjunctionDLConcept):
            return self.disjunction(concept)
        elif isinstance(concept, Restriction):
            return self.restriction(concept)
        elif isinstance(concept, ValueRestriction):
            return self.value_restriction(concept)
        else:
            raise NotImplementedError(type(concept))

    @abstractmethod
    def atomic_concept(self, concept: NC) -> Set[str]:
        raise NotImplementedError()

    @abstractmethod
    def negated_atomic_concept(self, concept: NNC) -> Set[str]:
        raise NotImplementedError()

    @abstractmethod
    def restriction(self, concept: Restriction) -> Set[str]:
        raise NotImplementedError()

    @abstractmethod
    def conjunction(self, concept: NC) -> Set[str]:
        raise NotImplementedError()

    @abstractmethod
    def disjunction(self, concept: NC) -> Set[str]:
        raise NotImplementedError()


class NWR(AbstractReasoner):
    def __init__(self, predictor, gamma=.60, all_named_individuals: Set[str] = None):
        super(NWR, self)
        self.predictor = predictor
        self.gamma = gamma
        self.all_named_individuals = all_named_individuals
        self.name = 'nwr'

    def atomic_concept(self, concept: NC) -> Set[str]:
        """ {x | f(x,type,concept) \ge \gamma} """
        assert isinstance(concept, NC)
        # (1) Compute scores for all entities.
        scores_for_all = self.predictor.predict(relations=['<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'],
                                                tail_entities=[concept.iri])
        # (2) Iterative (1) and return entities whose predicted score satisfies the condition.
        raw_results = {self.predictor.idx_to_entity[index] for index, flag in enumerate(scores_for_all >= self.gamma) if
                       flag}
        # (3) Remove non entity predictions.
        return {i for i in raw_results if i in self.all_named_individuals}

    def negated_atomic_concept(self, concept: NNC) -> Set[str]:
        assert isinstance(concept, NNC)
        return self.all_named_individuals - self.predict(concept.neg())

    def conjunction(self, concept: ConjunctionDLConcept) -> Set[str]:
        """ 	Conjunction   ⊓           & $C\sqcap D$    & $C^\mathcal{I}\cap D^\mathcal{I} """
        return self.predict(concept=concept.left).intersection(self.predict(concept=concept.right))

    def disjunction(self, concept: DisjunctionDLConcept) -> Set[str]:
        """ ⊔ """
        return self.predict(concept=concept.left).union(self.predict(concept=concept.right))

    def restriction(self, concept: Restriction) -> Set[str]:
        if concept.opt == '∃':
            return self.existential_restriction(role=concept.role_iri, filler_concept=concept.filler)
        elif concept.opt == '∀':
            return self.universal_restriction(role=concept.role_iri, filler_concept=concept.filler)
        else:
            raise ValueError(concept.str)

    def existential_restriction(self, role: str, filler_concept: str = None, filler_indv: Set[str] = None):
        """ \exists r.C  { x \mid \exists y. (x,y) \in r^I \land y \in C^I } """
        # (1) Find individuals satisfying filler y \in C^I.
        if filler_concept:
            filler_individuals = self.predict(concept=filler_concept)
        elif filler_indv:
            filler_individuals = filler_indv
        else:
            filler_individuals = self.all_named_individuals
        results = []
        for i in filler_individuals:
            scores_for_all = self.predictor.predict(relations=[role], tail_entities=[i])
            ids = (scores_for_all >= self.gamma).nonzero(as_tuple=True)[0].tolist()
            if len(ids) >= 1:
                results.extend(ids)
            else:
                continue
        return {self.predictor.idx_to_entity[i] for i in results}

    def universal_restriction(self, role: str, filler_concept: AbstractDLConcept):

        results = set()
        interpretation_of_filler = self.predict(filler_concept)
        # We should only consider the domain of the interpretation of the role.
        for i in self.all_named_individuals:
            # {SELECT ?var
            #   (count(?s2) as ?cnt2)
            #   WHERE { ?var r ?s2 }
            #   GROUP By ?var}
            scores_for_all = self.predictor.predict(head_entities=[i], relations=[role])
            raw_results = {self.predictor.idx_to_entity[index] for index, flag in
                           enumerate(scores_for_all >= self.gamma) if flag}
            cnt2 = {i for i in raw_results if i in self.all_named_individuals}

            # {SELECT ?var
            #   (count (?s1) as ?cn1)
            #   WHERE { ?var r ?s1 .
            #           \tau(C,?s1) .}
            #   GROUP BY ?var }
            cnt1 = cnt2.intersection(interpretation_of_filler)
            # jaccard
            if len(cnt1.intersection(cnt2)) / (len(cnt1.union(cnt2))) >= self.gamma:
                results.add(i)
        return results

    def value_restriction(self, concept: ValueRestriction):
        results = dict()
        for i in self.predict(concept.filler):
            scores_for_all = self.predictor.predict(relations=[concept.role_iri], tail_entities=[i])

            # (2) Iterative (1) and return entities whose predicted score satisfies the condition.
            raw_results = {self.predictor.idx_to_entity[index] for index, flag in
                           enumerate(scores_for_all >= self.gamma) if flag}
            # (3) Remove non entity predictions.
            for k in raw_results:
                if k in self.all_named_individuals:
                    results.setdefault(k, 1)
                    results[k] += 1
        if concept.opt == '≥':
            # at least
            return {k for k, v in results.items() if v >= concept.val}
        else:
            return {k for k, v in results.items() if v <= concept.val}


class CWR(AbstractReasoner):
    """ Closed World Assumption"""

    def __init__(self, database, all_named_individuals):
        super(CWR, self)
        self.database = database
        self.all_named_individuals = all_named_individuals
        self.name = 'CWR'

    def atomic_concept(self, concept: NC) -> Set[str]:
        """ Atomic concept (C)    C^I \⊆ ∆^I """
        assert isinstance(concept, NC)
        return set(self.database[(self.database['relation'] == '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') & (
                self.database['object'] == concept.iri)]['subject'].tolist())

    def negated_atomic_concept(self, concept: NNC) -> Set[str]:
        """ Negation (¬C) : ∆^I \ C^I  """
        assert isinstance(concept, NNC)
        return self.all_named_individuals - self.atomic_concept(concept=concept.neg())

    def conjunction(self, concept: ConjunctionDLConcept) -> Set[str]:
        """  Conjunction   (⊓) : C ⊓ D  : C^I ⊓ D^I """
        assert isinstance(concept, ConjunctionDLConcept)
        return self.atomic_concept(concept.left).intersection(self.atomic_concept(concept.right))

    def disjunction(self, concept: DisjunctionDLConcept) -> Set[str]:
        """  Disjunction   (⊔) : C ⊔ D  : C^I ⊔ D^I """
        assert isinstance(concept, DisjunctionDLConcept)
        return self.atomic_concept(concept.left).union(self.atomic_concept(concept.right))

    def restriction(self, concept: Restriction) -> Set[str]:
        if concept.opt == '∃':
            return self.existential_restriction(role=concept.role_iri, filler_concept=concept.filler)
        elif concept.opt == '∀':
            return self.universal_restriction(role=concept.role_iri, filler_concept=concept.filler)
        else:
            raise ValueError(concept.str)

    def existential_restriction(self, role: str, filler_concept, filler_indv: Set[str] = None):
        """ \exists r.C  { x \mid \exists y. (x,y) \in r^I \land y \in C^I } """
        # (1) All triples with a given role.
        triples_with_role = self.database[self.database['relation'] == role].to_records(index=False)
        # (2) All individuals having type C.
        if filler_concept:
            filler_individuals = self.predict(concept=filler_concept)
        elif filler_indv:
            filler_individuals = filler_indv
        else:
            filler_individuals = self.all_named_individuals
        # (3) {x | ( x r y ) and (y type C) }.
        return {spo[0] for spo in triples_with_role if spo[2] in filler_individuals}

    def universal_restriction(self, role: str, filler_concept: AbstractDLConcept):
        """ \forall r.C   &
        { x | \forall y. (x,y) \in r^I \implies y \in C^I \}  """
        # READ Towards SPARQL - Based Induction for Large - Scale RDF Data sets Technical Report for the details
        # http://svn.aksw.org/papers/2016/ECAI_SPARQL_Learner/tr_public.pdf
        results = set()
        filler_individuals = self.predict(filler_concept)

        domain_of_interpretation_of_relation = {_ for _ in self.database[(self.database['relation'] == role)][
            'subject'].tolist()}

        for i in domain_of_interpretation_of_relation:
            # {SELECT ?var
            #   (count(?s2) as ?cnt2)
            #   WHERE {?var r ?s2}
            #   GROUP By ?var}
            # All objects given subject and a relation
            cnt2 = {_ for _ in self.database[(self.database['subject'] == i) & (self.database['relation'] == role)][
                'object'].tolist()}
            # {SELECT ?var
            #   (count (?s1) as ?cn1)
            #   WHERE { ?var r ?s1 .
            #           \tau(C,?s1) .}
            #   GROUP BY ?var }
            cnt1 = cnt2.intersection(filler_individuals)
            if len(cnt1) == len(cnt2): # or cnt1==cnt2
                results.add(i)
        return results


class SPARQLCWR(AbstractReasoner):
    def __init__(self, url, name: str = 'sparqlcwr'):
        super(SPARQLCWR, self)
        self.url = url
        self.name = name

    def query(self, query: str):
        response = requests.post(self.url, data={
            'query': query})
        # Adding brackets
        return {'<' + i['var']['value'] + '>' for i in response.json()['results']['bindings']}

    def retrieve(self, concept):
        return self.query(converter.as_query("?var", parser.parse_expression(concept.str), False))

    def atomic_concept(self, concept: NC) -> Set[str]:
        """ {x | f(x,type,concept) \ge \gamma} """
        assert isinstance(concept, NC)
        return self.retrieve(concept)

    def negated_atomic_concept(self, concept: NNC)-> Set[str]:
        assert isinstance(concept, NNC)
        return self.retrieve(concept)

    def conjunction(self, concept) -> Set[str]:
        """  Conjunction   (⊓) : C ⊓ D  : C^I ⊓ D^I """
        return self.retrieve(concept)

    def disjunction(self, concept) -> Set[str]:
        """  Disjunction   (⊔) : C ⊔ D  : C^I ⊔ D^I """
        return self.retrieve(concept)

    def restriction(self, concept):
        return self.retrieve(concept)

    def value_restriction(self, concept: ValueRestriction) -> Set[str]:
        return self.retrieve(concept)
