import os
from pathlib import Path
from diskcache import Cache
from dotenv import load_dotenv
import requests
from langchain_core.documents import Document

from langchain_community.document_loaders import PDFPlumberLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

from database import embedding_record, insert_embedding
from utils.cache import cache
from utils.embedding import create_embedding

load_dotenv()
pdf_path = Path("./nke-10k-2023.pdf")


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


if __name__ == "__main__":
    splites = get_splitter_docs(pdf_path)
    for splite in splites:
        embedding = create_embedding(splite.page_content)

        if not embedding:
            assert False, "embedding 创建失败"

        insert_embedding(
            embedding_record(
                text=splite.page_content,
                embedding=embedding,
                metadata=str(splite.metadata),
            )
        )
        print("插入成功")
        break  # just test one
