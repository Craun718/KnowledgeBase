from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from loguru import logger as log
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Tuple

from database import (
    DocumentRecord,
    insert_records_batch,
)
from service.splitter import get_splitter_docs

load_dotenv()

insert_dir = Path("./data/files")
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
        insert_records_batch(docs_to_insert, batch_size=32)

        log.debug(f"{file_path.name} 处理并插入完成！")


def process_single_pdf(file_path: Path) -> Tuple[Path, List[DocumentRecord]]:
    """处理单个PDF文件，返回文件路径和文档记录列表

    Args:
        file_path: PDF文件路径

    Returns:
        包含文件路径和文档记录列表的元组
    """
    try:
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

        log.debug(f"{file_path.name} 文档分割完成，共 {len(docs_to_insert)} 个片段")
        return file_path, docs_to_insert

    except Exception as e:
        log.error(f"处理文件 {file_path.name} 时出错: {str(e)}")
        return file_path, []


def load_all_pdfs(max_workers: int = 4):
    """处理 `data/files` 下的所有 PDF 并批量插入到数据库。

    使用多线程并行处理PDF文件以提高性能，但保持数据库插入操作的同步以避免冲突。

    Args:
        max_workers: 最大工作线程数，默认为4
    """
    if not file_list:
        log.info("未找到PDF文件")
        return

    log.info(f"开始处理 {len(file_list)} 个PDF文件，使用 {max_workers} 个线程")

    # 使用线程锁保护数据库操作
    db_lock = threading.Lock()

    # 使用ThreadPoolExecutor进行并行处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有文件处理任务
        future_to_file = {
            executor.submit(process_single_pdf, file_path): file_path
            for file_path in file_list
        }

        # 使用tqdm显示总体进度
        with tqdm(total=len(file_list), desc="处理PDF文件") as pbar:
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]

                try:
                    processed_file_path, docs_to_insert = future.result()

                    if docs_to_insert:
                        # 使用锁保护数据库插入操作
                        with db_lock:
                            # 批量插入，batch_size设为32（API限制）
                            insert_records_batch(docs_to_insert, batch_size=32)
                            log.debug(
                                f"{processed_file_path.name} 处理并插入完成！共 {len(docs_to_insert)} 个文档片段"
                            )
                    else:
                        log.warning(f"{file_path.name} 处理失败或无有效内容")

                except Exception as e:
                    log.error(f"处理文件 {file_path.name} 时发生异常: {str(e)}")

                finally:
                    pbar.update(1)

    log.info("所有PDF文件处理完成！")
