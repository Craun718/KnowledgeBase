import json
from pathlib import Path
from dotenv import load_dotenv


from database import (
    document_record,
    insert_records_batch,
    similarity_search,
)
from service.embedding import get_splitter_docs

load_dotenv()
pdf_path = Path("./nke-10k-2023.pdf")


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
