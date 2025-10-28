from typing import List
import chromadb
import uuid

from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.types import Embedding
import numpy as np
from utils.embedding import create_embedding


class siliconflow_embeddingFunction(EmbeddingFunction):
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
    def __init__(self, text: str, embedding: List[float], metadata: str):
        self.text = text
        self.embedding = embedding
        self.metadata = metadata


def insert_embedding(doc: document_record) -> str:
    existing_docs = collection.get(where={"metadata.text": doc.metadata})
    if existing_docs["ids"]:
        print("Document already exists in the collection.")
        return existing_docs["ids"][0]

    id = str(uuid.uuid4())
    collection.add(
        ids=[id],
        documents=[doc.text],
        embeddings=[doc.embedding],
        metadatas=[{"metadata": doc.metadata}],
    )
    return id
