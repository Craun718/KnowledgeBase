import os
import requests
from loguru import logger as log
from fastapi import HTTPException, status


def llm_query(content: str) -> str:
    url = "https://api.siliconflow.cn/v1/chat/completions"

    payload = {
        "model": "THUDM/GLM-4-9B-0414",
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('siliconflow_token')}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)
    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"LLM API request failed: {response.text}",
        )

    result = response.json()["choices"][0]["message"]["content"]

    log.debug("Raw LLM Response:", result)

    return result


if __name__ == "__main__":
    llm_query("你好！")
