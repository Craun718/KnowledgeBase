import json
from typing import List
import uuid
import os
from fastapi import HTTPException, status
import requests

import numpy as np
from dotenv import load_dotenv

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.errors import NotFoundError
from chromadb.api.types import Embedding
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.embeddings.base import Embeddings as LangChainEmbeddings
from langchain_classic.storage import LocalFileStore
from tqdm import tqdm
from utils.cache import cache
from utils.hash import make_hash

load_dotenv()

store = LocalFileStore("./tmp/cache/")


class SiliconFlowEmbeddings(LangChainEmbeddings):
    """自定义 SiliconFlow embedding 类，兼容 LangChain 接口"""

    def __init__(self):
        self.model = "BAAI/bge-m3"
        self.base_url = "https://api.siliconflow.cn/v1"
        self.api_key = os.getenv("siliconflow_token")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""

        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.model,
            "input": texts,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers)
        if not response.ok:
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key for Embedding service",
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Embedding API request failed with status code {response.status_code}",
            )

        data = response.json()
        message = data.get("message")
        if message:
            assert False, f"Embedding API error: {message}"

        return [item["embedding"] for item in data["data"]] if data["data"] else []

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        return self.embed_documents([text])[0]


class CustomDocument:
    def __init__(self, content: str, doc_name: str, page_number):
        self.content = content
        self.doc_name = doc_name
        self.page_number = page_number

    def to_dict(self):
        return {
            "content": self.content,
            "doc_name": self.doc_name,
            "page_number": self.page_number,
        }


# 创建带缓存的 embedding 实例
underlying_embeddings = SiliconFlowEmbeddings()
cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings,
    store,
    key_encoder=make_hash,
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")

try:
    collection = chroma_client.get_collection("my_collection")
    if not collection:
        collection = chroma_client.create_collection(name="my_collection")
except NotFoundError:
    collection = chroma_client.create_collection(name="my_collection")


class DocumentRecord:
    metadata: dict

    def __init__(self, content: str, metadata: str | dict):
        self.content = content
        if isinstance(metadata, str):
            try:
                self.metadata = json.loads(metadata)
            except json.JSONDecodeError:
                self.metadata = {"text": metadata}
        elif isinstance(metadata, dict):
            self.metadata = metadata["metadata"] if "metadata" in metadata else metadata
            if isinstance(self.metadata, str):
                try:
                    self.metadata = json.loads(self.metadata)
                except json.JSONDecodeError:
                    self.metadata = {"text": self.metadata}
        else:
            raise ValueError("Metadata must be either a string or a dictionary.")

    def __dict__(self):
        return {
            "content": self.content,
            "metadata": self.metadata,
        }


def insert_record(doc: DocumentRecord) -> str:
    id = str(uuid.uuid4())
    doc_embedding = cached_embeddings.embed_query(doc.content)
    collection.add(
        ids=[id],
        documents=[doc.content],
        embeddings=[doc_embedding],
        metadatas=[doc.metadata],
    )
    return id


def insert_records_batch(docs: List[DocumentRecord], batch_size: int = 32) -> List[str]:
    """批量插入文档记录"""
    all_ids = []

    for i in tqdm(
        range(0, len(docs), batch_size), desc="Inserting batches", unit="batch"
    ):
        batch = docs[i : i + batch_size]

        # 批量生成ID
        batch_ids = [str(uuid.uuid4()) for _ in batch]

        # 批量生成embedding
        batch_contents = [doc.content for doc in batch]
        batch_embeddings = cached_embeddings.embed_documents(batch_contents)

        # 批量插入到collection
        collection.add(
            ids=batch_ids,
            documents=batch_contents,
            embeddings=batch_embeddings,  # type: ignore
            metadatas=[doc.metadata for doc in batch],
        )

        all_ids.extend(batch_ids)

    return all_ids


def similarity_search(query: str, limit: int = 5) -> List[DocumentRecord]:
    # 使用缓存的 embeddings 生成查询向量
    query_embedding = cached_embeddings.embed_query(query)
    query_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
    )
    if (not query_results["documents"]) or (not query_results["metadatas"]):
        return []

    documents_list = query_results["documents"][0]
    metadatas_list = query_results["metadatas"][0]

    if "distances" in query_results and query_results["distances"]:
        distances = query_results["distances"][0]
        # 创建 (distance, content, metadata) 的列表
        items = list(zip(distances, documents_list, metadatas_list))
        # 按距离升序排序（距离越小，越相似）
        items.sort(key=lambda x: x[0], reverse=True)
    else:
        # 如果没有距离信息，直接使用原始顺序
        items = list(zip([0] * len(documents_list), documents_list, metadatas_list))

    # 创建 DocumentRecord 列表
    documents = [
        DocumentRecord(
            content=content,
            metadata=dict(metadata),  # 转换为 dict
        )
        for _, content, metadata in items
    ]
    return documents


def extract_docs_has_single_term(term: str) -> List[DocumentRecord]:
    """Extract sentences containing the term from the text."""
    documents = similarity_search(f"包含{term}的句子", limit=10)

    results: List[DocumentRecord] = []
    for doc in documents:
        if term in doc.content:
            results.append(doc)

    print("Retrieved Documents:")
    print(f"Found {len(results)} documents containing the term.")

    return results
