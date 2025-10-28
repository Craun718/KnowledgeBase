import hashlib
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.cache import cache


@cache.memoize()
def get_splitter_docs(file_path: Path) -> list[Document]:
    loader = PDFPlumberLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512, chunk_overlap=64, add_start_index=True
    )

    all_splits = text_splitter.split_documents(docs)
    return all_splits
