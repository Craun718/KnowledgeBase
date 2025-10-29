from typing import List
from pydantic import BaseModel


class TermDefinition:
    def __init__(
        self, term: str, definition: str, documents: str, page: int, reason: str
    ):
        self.term = term
        self.definition = definition
        self.reason = reason
        self.documents = documents
        self.page = page

    def to_dict(self):
        return {
            "term": self.term,
            "definition": self.definition,
            "documents": self.documents,
            "page": self.page,
        }


class DefinitionResult(BaseModel):
    term: str
    definition: str
    documents: str
    page: int


class DefinitionResponse(BaseModel):
    result: List[DefinitionResult]


class RelationResult(BaseModel):
    term1: str
    term2: str
    relation: str
    reason: str
    documents: str
    page: int


class RelationResponse(BaseModel):
    result: List[RelationResult]


class TermRelation:
    def __init__(
        self,
        term1: str,
        term2: str,
        relation: str,
        documents: str,
        page: int,
        reason: str,
    ):
        self.term1 = term1
        self.term2 = term2
        self.relation = relation
        self.reason = reason
        self.documents = documents
        self.page = page
