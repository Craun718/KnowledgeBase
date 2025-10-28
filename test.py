import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document

from langchain_community.document_loaders import PDFPlumberLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from database import (
    document_record,
    insert_record,
    insert_records_batch,
    similarity_search,
)
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


if __name__ == "__main__":
    splites = get_splitter_docs(pdf_path)

    # 准备批量插入的文档记录
    docs_to_insert = []
    for splite in splites:
        docs_to_insert.append(
            document_record(
                content=splite.page_content,
                metadata=splite.metadata,
            )
        )

    # 批量插入，batch_size设为32（API限制）
    print(f"开始批量插入 {len(docs_to_insert)} 个文档块，batch_size=32")
    insert_records_batch(docs_to_insert, batch_size=32)

    print("所有切分块已插入到向量数据库中。")

    results = similarity_search(
        "How many distribution centers does Nike have in the US?"
    )

    print(json.dumps([doc.__dict__() for doc in results], indent=2, ensure_ascii=False))
