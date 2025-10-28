import spacy
from pathlib import Path

from config import self_dir

model_dir = (
    Path(self_dir)
    / "models"
    / "zh_core_web_lg-3.8.0"
    / "zh_core_web_lg"
    / "zh_core_web_lg-3.8.0"
)

nlp = spacy.load(model_dir)


def extract_terms(text):
    doc = nlp(text)
    return [
        chunk.text for chunk in doc.noun_chunks if len(chunk.text) > 1
    ]  # 提取名词短语作为候选术语


target_term_pair = ("人工智能", "就业结构")
