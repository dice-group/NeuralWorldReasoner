from abc import ABC, abstractmethod
from typing import Set
import requests
from owlapy.parser import DLSyntaxParser
from owlapy.owl2sparql.converter import Owl2SparqlConverter

parser = DLSyntaxParser("http://www.benchmark.org/family#")
converter = Owl2SparqlConverter()


class AbstractDLConcept(ABC):
    pass


class Restriction(AbstractDLConcept):
    def __init__(self, opt: str, role: str, filler):
        super(Restriction, self)
        assert opt == '∃' or opt == '∀'
        self.opt = opt
        self.role_iri = role
        self.filler = filler
        self.str = opt + role.split('#')[-1][:-1] + '.' + filler.str
        self.sparql = converter.as_query("?var", parser.parse_expression(self.str), False)


class ConjunctionDLConcept(AbstractDLConcept):
    def __init__(self, concept_a, concept_b):
        super(ConjunctionDLConcept, self)
        self.str = concept_a.str + " ⊓ " + concept_b.str
        self.left = concept_a
        self.right = concept_b
        self.sparql = "SELECT ?var  WHERE { " \
                      "?var <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>" + f" {concept_a.iri}" + " . " + \
                      "?var <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>" + f" {concept_b.iri}" + " . }"
        self.sparql = converter.as_query("?var", parser.parse_expression(self.str), False)


class DisjunctionDLConcept(AbstractDLConcept):
    def __init__(self, concept_a, concept_b):
        super(DisjunctionDLConcept, self)
        self.str = concept_a.str + " ⊔ " + concept_b.str
        self.left = concept_a
        self.right = concept_b
        self.sparql = "SELECT ?var  WHERE { " \
                      "OPTIONAL {?var <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>" + f" {concept_a.iri}" + " }" + \
                      "OPTIONAL {?var <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>" + f" {concept_b.iri}" + " }}"
        self.sparql = converter.as_query("?var", parser.parse_expression(self.str), False)


class NC(AbstractDLConcept):
    def __init__(self, iri):
        super(NC, self)
        self.iri = iri
        self.str = self.iri.split('#')[-1][:-1]
        self.sparql = converter.as_query("?var", parser.parse_expression(self.str), False)

    def neg(self):
        return NNC(iri=self.iri)

    def union(self, other: AbstractDLConcept):
        return ConjunctionDLConcept(self, other)

    def intersection(self, other: AbstractDLConcept):
        return DisjunctionDLConcept(self, other)


class NNC(AbstractDLConcept):
    def __init__(self, iri: str):
        super(NNC, self)
        self.neg_iri = iri
        self.str = "¬" + iri.split('#')[-1][:-1]
        self.sparql = converter.as_query("?var", parser.parse_expression(self.str), False)
        # self.sparql = "SELECT ?var  { ?var ?p <http://www.w3.org/2002/07/owl#NamedIndividual>" + "FILTER NOT EXISTS { ?var <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> " + f"{self.neg_iri}" + "}}"

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
        else:
            raise NotImplementedError(type(concept))

    @abstractmethod
    def atomic_concept(self, concept: NC) -> Set[str]:
        raise NotImplementedError()

    @abstractmethod
    def negated_atomic_concept(self, concept: NNC) -> Set[str]:
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

    def negated_atomic_concept(self, concept: NNC):
        assert isinstance(concept, NNC)

        return self.all_named_individuals - self.atomic_concept(concept=concept.base)

    def conjunction(self, concept_str: str, other: str) -> Set[str]:
        """ 	Conjunction   ⊓           & $C\sqcap D$    & $C^\mathcal{I}\cap D^\mathcal{I} """
        return self.atomic_concept(concept_str).intersection(self.atomic_concept(other))

    def disjunction(self, concept_str: str, other: str) -> Set[str]:
        """ ⊔ """
        return self.atomic_concept(concept_str).union(self.atomic_concept(other))

    def existential_restriction(self, role: str, filler_concept: str = None, filler_indv: Set[str] = None):
        """ \exists r.C  { x \mid \exists y. (x,y) \in r^I \land y \in C^I } """
        # (1) Find individuals satisfying filler y \in C^I.
        if filler_concept:
            filler_individuals = self.atomic_concept(concept=filler_concept)
        elif filler_indv:
            filler_individuals = filler_indv
        else:
            filler_individuals = self.all_named_individuals

        results = []
        for i in filler_individuals:
            scores_per_indv = self.predictor.predict(relations=[role], tail_entities=[i])

            ids = (scores_per_indv >= self.gamma).nonzero(as_tuple=True)[0].tolist()
            if len(ids) >= 1:
                results.extend(ids)
            else:
                continue
        return {self.predictor.idx_to_entity[i] for i in results}

    def universal_restriction(self, role: str, filler_concept: str):
        """ \forall r.C   &

        (1) \forall hasChild.Top
        \neg Top => \bot

        \forall hasChild.Top
        { x | \forall y. (x,y) \in r^I \implies y \in C^I \}  """
        # RECALL : https://github.com/SmartDataAnalytics/DL-Learner/blob/a7cd4441e52b6e54aefdea33a4914e9132ebfd97/components-core/src/main/java/org/dllearner/reasoning/ClosedWorldReasoner.java#L1058
        # \forall r.\bot     \equiv   \neg \exists r.\top

        # (1) Compute individuals belonging to the negation of the filler .
        individuals_neg_filler_concept = self.negated_atomic_concept(concept=filler_concept)
        # (2) Compute individuals beloning to the \exist r. neg C
        # (3) Domain - (2)
        return self.all_named_individuals - self.existential_restriction(role=role,
                                                                         filler_indv=individuals_neg_filler_concept)


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

    def restriction(self, concept)->Set[str]:
        if concept.opt == '∃':
            return self.existential_restriction(role=concept.role_iri, filler_concept=concept.filler)
        elif concept.opt == '∀':
            return self.universal_restriction(role=concept.role_iri, filler_concept=concept.filler)
        else:
            raise ValueError(concept)

    def conjunction(self, concept: ConjunctionDLConcept) -> Set[str]:
        """  Conjunction   (⊓) : C ⊓ D  : C^I ⊓ D^I """
        assert isinstance(concept, ConjunctionDLConcept)
        return self.atomic_concept(concept.left).intersection(self.atomic_concept(concept.right))

    def disjunction(self, concept: DisjunctionDLConcept) -> Set[str]:
        """  Disjunction   (⊔) : C ⊔ D  : C^I ⊔ D^I """
        assert isinstance(concept, DisjunctionDLConcept)
        return self.atomic_concept(concept.left).union(self.atomic_concept(concept.right))

    def existential_restriction(self, role: str, filler_concept: str = None, filler_indv: Set[str] = None):
        """ \exists r.C  { x \mid \exists y. (x,y) \in r^I \land y \in C^I } """
        # (1) All triples with a given role.
        triples_with_role = self.database[self.database['relation'] == role].to_records(index=False)
        # (2) All individuals having type C.
        if filler_concept:
            filler_individuals = self.atomic_concept(concept=filler_concept)
        elif filler_indv:
            filler_individuals = filler_indv
        else:
            filler_individuals = self.all_named_individuals
        # (3) {x | ( x r y ) and (y type C) }.
        return {spo[0] for spo in triples_with_role if spo[2] in filler_individuals}

    def universal_restriction(self, role: str, filler_concept: AbstractDLConcept):
        """ \forall r.C   &
        { x | \forall y. (x,y) \in r^I \implies y \in C^I \}  """
        # RECALL : https://github.com/SmartDataAnalytics/DL-Learner/blob/a7cd4441e52b6e54aefdea33a4914e9132ebfd97/components-core/src/main/java/org/dllearner/reasoning/ClosedWorldReasoner.java#L1058
        # \forall r.\bot     \equiv   \neg \exists r.\top

        # (1) Compute individuals belonging to the negation of the filler .

        individuals_neg_filler_concept = self.all_named_individuals - self.predict(filler_concept)
        # (2) Compute individuals beloning to the \exist r. neg C
        # (3) Domain - (2)
        return self.all_named_individuals - self.existential_restriction(role=role,
                                                                         filler_indv=individuals_neg_filler_concept)


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
        return self.query(concept.sparql)

    def atomic_concept(self, concept: NC) -> Set[str]:
        """ {x | f(x,type,concept) \ge \gamma} """
        assert isinstance(concept, NC)
        return self.retrieve(concept)

    def negated_atomic_concept(self, concept: NNC):
        """

        :param concept:
        :return:
        """
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
