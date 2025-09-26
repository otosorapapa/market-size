"""Utility helpers for mapping free-text industries to JSIC codes."""

from __future__ import annotations

import difflib
import functools
from pathlib import Path
from typing import Dict, List

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "jsic_seed.csv"


def load_seed_dataframe() -> pd.DataFrame:
    """Load seed JSIC data into a DataFrame."""

    df = pd.read_csv(DATA_PATH)
    df["keywords"] = df["keywords"].fillna("")
    return df


@functools.lru_cache(maxsize=1)
def _seed_records() -> List[Dict[str, str]]:
    df = load_seed_dataframe()
    return df.to_dict(orient="records")


def _score(query: str, keywords: str) -> float:
    a = query.lower()
    b = keywords.lower()
    ratio = difflib.SequenceMatcher(a=a, b=b).ratio()
    if query in keywords:
        ratio += 0.2
    return min(ratio, 1.0)


def guess_jsic(industry_name: str, limit: int = 5) -> List[Dict[str, str]]:
    """Return the best matching JSIC candidates for the input industry name."""

    if not industry_name:
        return []
    query = industry_name.strip().lower()
    ranked = []
    for item in _seed_records():
        label = str(item.get("label", ""))
        keywords = str(item.get("keywords", ""))
        score = _score(query, f"{label},{keywords}")
        if query in label.lower():
            score += 0.3
        ranked.append({
            "label": label,
            "jsic_code": str(item.get("jsic_code", "")),
            "score": min(score, 1.0),
        })
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]

