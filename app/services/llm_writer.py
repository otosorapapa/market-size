"""Generate strategic analysis narratives using OpenAI models."""

from __future__ import annotations

import json
import os
from typing import Dict

import requests

try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover
    st = None  # type: ignore

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def _load_credentials() -> Dict[str, str]:
    if st is not None and "OPENAI_API_KEY" in st.secrets:
        return {
            "api_key": st.secrets["OPENAI_API_KEY"],
            "model": st.secrets.get("OPENAI_MODEL", "gpt-4o-mini"),
        }
    return {
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    }


def _build_prompt(context: Dict[str, str]) -> Dict[str, str]:
    bullet_points = []
    for key, value in context.items():
        bullet_points.append(f"- {key}: {value}")
    facts = "\n".join(bullet_points)
    instructions = (
        "あなたは日本の中小企業診断士です。提供された統計指標に基づき、PEST、3C、5Forces、審査員向け1枚サマリーを日本語で作成してください。"
        "数値は必ず指標名・年・地域と共に明記し、出典（e-Stat）とNowcast推定値である場合の注意喚起を盛り込んでください。"
    )
    prompt = f"{instructions}\n根拠データ:\n{facts}"
    return {
        "role": "user",
        "content": prompt,
    }


def generate_sections(context: Dict[str, str]) -> Dict[str, str]:
    """Generate analysis sections using OpenAI."""

    creds = _load_credentials()
    if not creds["api_key"]:
        raise RuntimeError("OpenAI APIキーが設定されていません。secrets.tomlを確認してください。")

    payload = {
        "model": creds["model"],
        "messages": [
            {
                "role": "system",
                "content": "専門的でありながら中小企業の審査担当者に伝わりやすい文体で、1500文字以内に収めてください。セクションごとに見出しを付けてください。",
            },
            _build_prompt(context),
        ],
        "max_tokens": 900,
        "temperature": 0.4,
    }

    headers = {
        "Authorization": f"Bearer {creds['api_key']}",
        "Content-Type": "application/json",
    }
    response = requests.post(OPENAI_URL, headers=headers, data=json.dumps(payload), timeout=60)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    sections = {
        "pest": "",
        "threec": "",
        "fiveforces": "",
        "summary1pager": "",
    }
    current = None
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        lowered = line.lower()
        if "pest" in lowered:
            current = "pest"
            sections[current] = line
        elif "3c" in lowered:
            current = "threec"
            sections[current] = line
        elif "5" in lowered and "forces" in lowered:
            current = "fiveforces"
            sections[current] = line
        elif "サマリー" in line or "まとめ" in line:
            current = "summary1pager"
            sections[current] = line
        elif current:
            sections[current] += "\n" + line
    return sections

