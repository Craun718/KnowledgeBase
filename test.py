import os
from pathlib import Path
from diskcache import Cache
from dotenv import load_dotenv
import requests
from langchain_core.documents import Document

from langchain_community.document_loaders import PDFPlumberLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.cache import cache

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


@cache.memoize()
def create_embeddings(content: str):
    # 1024 dimensions
    url = "https://api.siliconflow.cn/v1/embeddings"
    token = os.getenv("siliconflow_token")
    payload = {
        "model": "BAAI/bge-large-zh-v1.5",
        "input": content,
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    print(response.json())


if __name__ == "__main__":
    splites = get_splitter_docs(pdf_path)
    for splite in splites:
        create_embeddings(splite.page_content)
