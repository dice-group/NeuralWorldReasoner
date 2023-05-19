from abc import ABC
from typing import Set
import requests


class AbstractReasoner(ABC):
    pass


class NWR:
    def __init__(self, predictor, gamma=.60, all_named_individuals: Set[str] = None):
        self.predictor = predictor
        self.gamma = gamma
        self.all_named_individuals = all_named_individuals
        self.name = 'nwr'

    def atomic_concept(self, concept: str) -> Set[str]:
        """ {x | f(x,type,concept) \ge \gamma} """
        # (1) Compute scores for all entities.
        scores_for_all = self.predictor.predict(relations=['<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'],
                                                tail_entities=[concept])
        # (2) Iterative (1) and return entities whose predicted score satisfies the condition.
        raw_results = {self.predictor.idx_to_entity[index] for index, flag in enumerate(scores_for_all >= self.gamma) if
                       flag}
        # (3) Remove non entity predictions.
        return {i for i in raw_results if i in self.all_named_individuals}

    def negated_atomic_concept(self, concept: str):
        return self.all_named_individuals - self.atomic_concept(concept=concept)

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


class CWR:
    """ Closed World Assumption"""

    def __init__(self, database, all_named_individuals):
        self.database = database
        self.all_named_individuals = all_named_individuals
        self.name = 'cwr'

    def atomic_concept(self, concept: str) -> Set[str]:
        """ Atomic concept (C)    C^I \⊆ ∆^I """
        return set(self.database[(self.database['relation'] == '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>') & (
                self.database['object'] == concept)]['subject'].tolist())

    def conjunction(self, concept_str: str, other: str) -> Set[str]:
        """  Conjunction   (⊓) : C ⊓ D  : C^I ⊓ D^I """
        return self.atomic_concept(concept_str).intersection(self.atomic_concept(other))

    def disjunction(self, concept_str: str, other: str) -> Set[str]:
        """  Disjunction   (⊔) : C ⊔ D  : C^I ⊔ D^I """
        return self.atomic_concept(concept_str).union(self.atomic_concept(other))

    def negated_atomic_concept(self, concept: str) -> Set[str]:
        """ Negation (¬C) : ∆^I \ C^I  """
        return self.all_named_individuals - self.atomic_concept(concept=concept)

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
            filler_individuals = all_named_indv
        # (3) {x | ( x r y ) and (y type C) }.
        return {spo[0] for spo in triples_with_role if spo[2] in filler_individuals}

    def universal_restriction(self, role: str, filler_concept: str):
        """ \forall r.C   &
        { x | \forall y. (x,y) \in r^I \implies y \in C^I \}  """
        # RECALL : https://github.com/SmartDataAnalytics/DL-Learner/blob/a7cd4441e52b6e54aefdea33a4914e9132ebfd97/components-core/src/main/java/org/dllearner/reasoning/ClosedWorldReasoner.java#L1058
        # \forall r.\bot     \equiv   \neg \exists r.\top

        # (1) Compute individuals belonging to the negation of the filler .
        individuals_neg_filler_concept = self.negated_atomic_concept(concept=filler_concept)
        # (2) Compute individuals beloning to the \exist r. neg C
        # (3) Domain - (2)
        return self.all_named_individuals - self.existential_restriction(role=role,
                                                                         filler_indv=individuals_neg_filler_concept)


class SPARQLCWR:
    def __init__(self, url, name: str = 'sparqlcwr'):
        self.url = url
        self.name = name

    def retrieve(self, query: str):
        response = requests.post(self.url, data={
            'query': query})
        # Adding brackets
        return {'<' + i['s']['value'] + '>' for i in response.json()['results']['bindings']}

    def atomic_concept(self, concept: str) -> Set[str]:
        """ {x | f(x,type,concept) \ge \gamma} """
        query = "SELECT ?s  { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
        query += f"{concept}" + "}"
        return self.retrieve(query)

    def negated_atomic_concept(self, concept: str):
        """

        :param concept:
        :return:
        """
        query = "SELECT ?s  { ?s ?p <http://www.w3.org/2002/07/owl#NamedIndividual> ." \
                "FILTER NOT EXISTS { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
        query+=f"{concept}" + "}}"
        return self.retrieve(query)
