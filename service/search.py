from database import extract_docs_has_single_term
from utils.definition import extract_term_definition


def get_definition(query: str):
    docs = extract_docs_has_single_term(query)
    return extract_term_definition(query, docs)
