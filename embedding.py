import tarfile
import lzma
from pathlib import Path
from tqdm import tqdm
from loguru import logger as log

from database import DocumentRecord, insert_records_batch
from service.splitter import get_splitter_docs


def init_embedding_db():
    """初始化嵌入数据库：解压文件并导入所有PDF到ChromaDB"""

    # 定义路径
    data_dir = Path("./data/files")
    tar_xz_file = data_dir / "files.tar.xz"

    # 检查压缩文件是否存在
    if not tar_xz_file.exists():
        log.error(f"压缩文件不存在: {tar_xz_file}")
        return

    log.info("开始解压文件...")

    try:
        # 解压 .tar.xz 文件
        with lzma.open(tar_xz_file, "rb") as xz_file:
            with tarfile.open(fileobj=xz_file, mode="r") as tar:
                # 解压到 data/files 目录
                tar.extractall(path=data_dir)

        log.info("文件解压完成")

        # 获取所有PDF文件
        pdf_files = list(data_dir.glob("*.pdf"))
        log.info(f"找到 {len(pdf_files)} 个PDF文件")

        if not pdf_files:
            log.warning("没有找到PDF文件")
            return

        # 处理每个PDF文件
        for file_path in tqdm(pdf_files, desc="处理PDF文件"):
            try:
                log.debug(f"正在处理: {file_path.name}")

                # 使用分割器处理文档
                splits = get_splitter_docs(file_path)

                # 准备批量插入的文档记录
                docs_to_insert = []
                for split in splits:
                    docs_to_insert.append(
                        DocumentRecord(
                            content=split.page_content,
                            metadata=split.metadata,
                        )
                    )

                # 批量插入，batch_size设为32（API限制）
                insert_records_batch(docs_to_insert, batch_size=32)

                log.debug(f"{file_path.name} 处理并插入完成！")

            except Exception as e:
                log.error(f"处理文件 {file_path.name} 时出错: {str(e)}")
                continue

        log.info("所有PDF文件处理完成！")

    except Exception as e:
        log.error(f"解压或处理文件时出错: {str(e)}")
        raise
