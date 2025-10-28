import json
from typing import List
import chromadb
import uuid

from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.errors import NotFoundError
from chromadb.api.types import Embedding
import numpy as np
from utils.embedding import create_embedding
from utils.cache import cache


class siliconflow_embeddingFunction(EmbeddingFunction):

    @cache.memoize()
    def __call__(self, input: Documents) -> Embeddings:
        embeddings: List[Embedding] = []
        for doc in input:
            embedding = create_embedding(doc)
            embeddings.append(np.array(embedding, dtype=np.float32))
        return embeddings


chroma_client = chromadb.PersistentClient(path="./chroma_db")

try:
    collection = chroma_client.get_collection("my_collection")
    if not collection:
        collection = chroma_client.create_collection(
            name="my_collection", embedding_function=siliconflow_embeddingFunction()
        )
except NotFoundError:
    collection = chroma_client.create_collection(
        name="my_collection", embedding_function=siliconflow_embeddingFunction()
    )


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


def insert_embedding(doc: document_record) -> str:
    existing_docs = collection.get(where={"metadata": {"$eq": doc.metadata}})
    if existing_docs["ids"]:
        return existing_docs["ids"][0]

    id = str(uuid.uuid4())
    collection.add(
        ids=[id],
        documents=[doc.content],
        metadatas=[{"metadata": doc.metadata}],
    )
    return id


def similarity_search(query: str, limit: int = 5) -> List[document_record]:
    query_embedding = siliconflow_embeddingFunction()([query])[0]
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
