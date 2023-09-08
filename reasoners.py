from abstract_reasoner import AbstractReasoner
from typing import Set
from util import jaccard_similarity, compute_prediction, evaluate_results
from dl_concepts import *
import dicee
import requests


class NWR(AbstractReasoner):
    def __init__(self, predictor: dicee.KGE, gammas=None, all_named_individuals: Set[str] = None):
        super(NWR, self)
        self.predictor = predictor
        self.gammas = gammas
        self.all_named_individuals = all_named_individuals
        self.name = 'nwr'

    def atomic_concept(self, concept: NC) -> Set[str]:
        """ {x | f(x,type,concept) \ge \gamma} """
        assert isinstance(concept, NC)
        # (1) Compute scores for all entities.
        scores_for_all = self.predictor.predict(r=['<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'],
                                                t=[concept.iri])
        # (2) Iterative (1) and return entities whose predicted score satisfies the condition.
        raw_results = {self.predictor.idx_to_entity[index] for index, flag in
                       enumerate(scores_for_all >= self.gammas['NC']) if
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

    def existential_restriction(self, role: str, filler_concept: str = None, filler_individuals: Set[str] = None):
        """ \exists r.C  { x \mid \exists y. (x,y) \in r^I \land y \in C^I }

        ∃ hasSibling.Female
                {?var r ?s.} ∪ {?s type C}

        SELECT DISTINCT ?var
        WHERE {
                    ?var <http://www.benchmark.org/family#hasSibling> ?s_1 .
                    (1) ?s_1 a <http://www.benchmark.org/family#Female> .  }


        """
        # (1) Find individuals that are likeliy y \in C^I.
        if filler_concept:
            filler_individuals = self.predict(concept=filler_concept)
        elif filler_individuals is not None:
            filler_individuals = filler_individuals
        else:
            filler_individuals = self.all_named_individuals

        results = set()
        # (2) For each filler individual
        for i in filler_individuals:
            # (2.1) Assign scores for all subjects.
            scores_for_all = self.predictor.predict(r=[role], t=[i])
            ids = (scores_for_all >= self.gammas['Exists']).nonzero(as_tuple=True)[0].tolist()
            if len(ids) >= 1:
                results.update(set(ids))
            else:
                continue
        return {self.predictor.idx_to_entity[i] for i in results}

    def old_universal_restriction(self, role: str, filler_concept: AbstractDLConcept):

        results = set()
        interpretation_of_filler = self.predict(filler_concept)
        # We should only consider the domain of the interpretation of the role.
        for i in self.all_named_individuals:
            # {SELECT ?var
            #   (count(?s2) as ?cnt2)
            #   WHERE { ?var r ?s2 }
            #   GROUP By ?var}
            scores_for_all = self.predictor.predict(h=[i], r=[role]).flatten()
            raw_results = {self.predictor.idx_to_entity[index] for index, flag in
                           enumerate(scores_for_all >= self.gammas['Forall']) if flag}
            # Demir hasSibling {......}
            cnt2 = {i for i in raw_results if i in self.all_named_individuals}

            # {SELECT ?var
            #   (count (?s1) as ?cn1)
            #   WHERE { ?var r ?s1 .
            #           \tau(C,?s1) .}
            #   GROUP BY ?var }
            # Demir hasSibling {......}
            cnt1 = cnt2.intersection(interpretation_of_filler)

            cnt1_and_cnt2 = cnt1.intersection(cnt2)
            cnt1_or_cnt2 = cnt1.union(cnt2)
            if len(cnt1_and_cnt2) == 0 and len(cnt1_or_cnt2) == 0:
                # if both empty
                results.add(i)
            elif len(cnt1_and_cnt2) == 0 or len(cnt1_or_cnt2) == 0:
                # if only one of them is empty
                continue
            elif len(cnt1_and_cnt2) / len(cnt1_or_cnt2) >= self.gammas['Forall']:
                # if none of them empty
                results.add(i)
            else:
                continue
        return results

    def universal_restriction(self, role: str, filler_concept: AbstractDLConcept):
        return self.all_named_individuals.difference(
            self.existential_restriction(role=role, filler_concept=filler_concept.neg()))

    def value_restriction(self, concept: ValueRestriction):
        results = dict()
        for i in self.predict(concept.filler):
            scores_for_all = self.predictor.predict(r=[concept.role_iri], t=[i])

            # (2) Iterative (1) and return entities whose predicted score satisfies the condition.
            raw_results = {self.predictor.idx_to_entity[index] for index, flag in
                           enumerate(scores_for_all >= self.gammas['Value']) if flag}
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

    def find_gammas(self, gammas, concepts, true_func):
        for (name, i) in concepts:
            print(f'Searching gamma for {name}')
            # Finding a good gamma
            best_sim = 0.0
            best_gamma = 0.0
            for gamma in gammas:
                self.gammas[name] = gamma
                df = evaluate_results(true_results=compute_prediction(i, predictor=true_func),
                                      predictions=compute_prediction(i, predictor=self))

                avg_sim = df[['Similarity']].mean().values[0]
                # print(f"Gamma:{gamma}\t Sim:{avg_sim}")
                if avg_sim > best_sim:
                    best_gamma = gamma
                    best_sim = avg_sim
                    print(f"Current Best Gamma:{best_gamma}\t for {name} Sim:{best_sim}")

            print(f"Best Gamma:{best_gamma}\t for {name} Sim:{best_sim}")
            self.gammas[name] = best_gamma


class HermiT(AbstractReasoner):
    def __init__(self, url):
        super(HermiT, self)
        self.url = url
        self.name = 'HermiT'

    def retrieve(self, concept) -> Set[str]:
        """
        perform concept retrieval
        :param concept:
        :return:
        """
        try:
            return {i for i in
                    requests.post('http://localhost:8080/hermit', data=concept.manchester_str).json()['individuals']}
        except requests.exceptions.JSONDecodeError:
            print('JSON Decoding Error')
            print(concept.manchester_str)
            return set()

    def atomic_concept(self, concept: NC) -> Set[str]:
        """ {x | f(x,type,concept) \ge \gamma} """
        assert isinstance(concept, NC)
        return self.retrieve(concept)

    def negated_atomic_concept(self, concept: NNC) -> Set[str]:
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


class SPARQLCWR(AbstractReasoner):
    def __init__(self, url, name: str = 'sparqlcwr'):
        super(SPARQLCWR, self)
        self.url = url
        self.name = name
        self.all_individuals = self.query("PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
                                          "SELECT DISTINCT ?var\n"
                                          "WHERE {?var a owl:NamedIndividual.}")

    def query(self, query: str) -> Set[str]:
        """
        Perform a SPARQL query
        :param query:
        :return:
        """
        response = requests.post(self.url, data={
            'query': query})
        # Adding brackets
        return {'<' + i['var']['value'] + '>' for i in response.json()['results']['bindings']}

    def retrieve(self, concept) -> Set[str]:
        """
        perform concept retrieval
        :param concept:
        :return:
        """
        if isinstance(concept, Restriction) and concept.opt == '∀':
            # A concept retrieval for ∀ r.C is performed by \neg \∃ r. ∃C
            # given '∀' r.C, convert it into \neg r. \neg C
            sparql_query = converter.as_query("?var", parser.parse_expression(
                Restriction(opt="∃", role=concept.role_iri, filler=concept.filler.neg()).str), False)
            return self.all_individuals.difference(self.query(sparql_query))
        else:
            sparql_query = converter.as_query("?var", parser.parse_expression(concept.str), False)
            return self.query(sparql_query)

    def atomic_concept(self, concept: NC) -> Set[str]:
        """ {x | f(x,type,concept) \ge \gamma} """
        assert isinstance(concept, NC)
        return self.retrieve(concept)

    def negated_atomic_concept(self, concept: NNC) -> Set[str]:
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
        raise NotImplementedError('Rewrite this part by using existential')
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
            if len(cnt1) == len(cnt2):  # or cnt1==cnt2
                results.add(i)
        return results
