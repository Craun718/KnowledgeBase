import json
from typing import List
import chromadb
import uuid

from chromadb import Documents, EmbeddingFunction, Embeddings
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

collection = chroma_client.get_collection("my_collection")
if not collection:
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
