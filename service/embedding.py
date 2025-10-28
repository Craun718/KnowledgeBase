from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.cache import cache


def load_pdf(file_path: Path) -> list[Document]:
    loader = PDFPlumberLoader(file_path)

    docs = loader.load()
    print(f"文档页数: {len(docs)}")
    return docs


def splitter_docs(docs: list[Document]) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )

    all_splits = text_splitter.split_documents(docs)
    print(f"文档切分后总块数: {len(all_splits)}")
    return all_splits


@cache.memoize()
def get_splitter_docs(file_path: Path) -> list[Document]:
    loader = PDFPlumberLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )

    all_splits = text_splitter.split_documents(docs)
    return all_splits
