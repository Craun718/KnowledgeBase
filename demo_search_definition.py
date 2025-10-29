import json
from database import (
    extract_docs_has_single_term,
)
from utils.definition import extract_term_definition


word = "海洋灾害"


if __name__ == "__main__":
    docs = extract_docs_has_single_term(word)
    result = extract_term_definition(word, docs)

    if result is None:
        print("未找到相关定义。")
        exit(0)

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
