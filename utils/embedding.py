import os
import requests
from .cache import cache


@cache.memoize()
def create_embedding(content: str) -> list[float] | None:
    # 1024 dimensions
    url = "https://api.siliconflow.cn/v1/embeddings"
    token = os.getenv("siliconflow_token")
    payload = {
        "model": "BAAI/bge-large-zh-v1.5",
        "input": content,
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    if response.ok is False:
        print(response.status_code, response.text)
        assert False, f"embedding 创建失败!"

    data = response.json()

    return data["data"][0]["embedding"] if data["data"] else None
