import hashlib
from pathlib import Path

from loguru import logger as log

from langchain_core.documents import Document
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_splitter_docs(file_path: Path) -> list[Document]:
    loader = PDFPlumberLoader(file_path)
    docs = loader.load()

    # 为每个文档页码加1（从1开始计数）
    for doc in docs:
        doc.metadata["page"] += 1
        doc.metadata["source"] = file_path.stem

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512, chunk_overlap=64, add_start_index=True
    )

    all_splits = text_splitter.split_documents(docs)
    return all_splits
