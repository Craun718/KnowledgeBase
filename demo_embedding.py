import json
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm


from database import (
    DocumentRecord,
    insert_records_batch,
)
from service.splitter import get_splitter_docs

load_dotenv()

insert_dir = Path("../训练集")
file_list = list(insert_dir.glob("*.pdf"))

if __name__ == "__main__":
    for file_path in tqdm(file_list):
        splites = get_splitter_docs(file_path)

        # 准备批量插入的文档记录
        docs_to_insert = []
        for splite in splites:
            docs_to_insert.append(
                DocumentRecord(
                    content=splite.page_content,
                    metadata=splite.metadata,
                )
            )

        # 批量插入，batch_size设为32（API限制）
        print(f"开始批量插入 {len(docs_to_insert)} 个文档块，batch_size=32")
        # insert_records_batch(docs_to_insert, batch_size=32)
        insert_records_batch(docs_to_insert, batch_size=32)

        print(f"{file_path.name} 处理并插入完成！")
