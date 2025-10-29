from database import extract_docs_has_both_term
from utils.relation import extract_term_relation


target_term_pair = ("海洋灾害", "海洋灾害应急")


if __name__ == "__main__":
    # 步骤1：获取包含两个术语的文档
    context_docs = extract_docs_has_both_term(target_term_pair)
    print(f"用于分析的上下文文档数：{len(context_docs)}")

    # 步骤2：提取术语关系
    relation_result = extract_term_relation(
        term1=target_term_pair[0], term2=target_term_pair[1], docs=context_docs
    )
