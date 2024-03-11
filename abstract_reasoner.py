from abc import ABC, abstractmethod
from typing import Set

from owlapy.model import OWLObjectIntersectionOf, OWLObjectUnionOf

from dl_concepts import *


class AbstractReasoner(ABC):
    def predict(self, concept) -> Set[str]:
        if isinstance(concept, NC):
            return self.atomic_concept(concept)
        elif isinstance(concept, NNC):
            return self.negated_atomic_concept(concept)
        elif isinstance(concept, OWLObjectIntersectionOf):
            return self.conjunction(concept)
        elif isinstance(concept, OWLObjectUnionOf):
            return self.disjunction(concept)
        elif isinstance(concept, Restriction):
            return self.restriction(concept)
        elif isinstance(concept, ValueRestriction):
            return self.value_restriction(concept)
        else:
            # TODO: need to implement for other implementation classes of AbstractDLConcept
            # the current solution works only for SPARQLCWR
            self.retrieve_from_dl_concept(concept)

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

    @abstractmethod
    def retrieve_from_dl_concept(self, concept):
        pass
