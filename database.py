import json
from typing import List
import uuid
import os
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
            raise Exception(response.text)

        data = response.json()
        message = data.get("message")
        if message:
            assert False, f"Embedding API error: {message}"

        return [item["embedding"] for item in data["data"]] if data["data"] else []

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        return self.embed_documents([text])[0]


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


class document_record:
    def __init__(self, content: str, metadata: str | dict):
        self.content = content
        if isinstance(metadata, str):
            self.metadata = metadata
        elif isinstance(metadata, dict):
            self.metadata = json.dumps(metadata, ensure_ascii=False)
        else:
            raise ValueError("Metadata must be either a string or a dictionary.")

    def __dict__(self):
        return {
            "content": self.content,
            "metadata": json.loads(self.metadata),
        }


def insert_record(doc: document_record) -> str:
    id = str(uuid.uuid4())
    doc_embedding = cached_embeddings.embed_query(doc.content)
    collection.add(
        ids=[id],
        documents=[doc.content],
        embeddings=[doc_embedding],
        metadatas=[{"metadata": doc.metadata}],
    )
    return id


def insert_records_batch(
    docs: List[document_record], batch_size: int = 32
) -> List[str]:
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
            metadatas=[{"metadata": doc.metadata} for doc in batch],
        )

        all_ids.extend(batch_ids)

    return all_ids


def similarity_search(query: str, limit: int = 5) -> List[document_record]:
    # 使用缓存的 embeddings 生成查询向量
    query_embedding = cached_embeddings.embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
    )
    if (not results["documents"]) or (not results["metadatas"]):
        return []

    documents = [
        document_record(
            content=content,
            # 先转为 JSON 字符串，再解析为 dict（处理非 dict 类型）
            metadata=json.loads(json.dumps(metadata["metadata"])),
        )
        for content, metadata in zip(results["documents"][0], results["metadatas"][0])
    ]
    return documents
