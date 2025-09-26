"""Layout helpers for the Streamlit dashboard."""

from __future__ import annotations

from typing import Dict, Tuple

import streamlit as st


FOOTER_TEXT = "統計出典：政府統計の総合窓口（e-Stat）。二次利用ポリシー遵守。 / 年次統計の最新値推定（Nowcast）は月次指標による近似。参考値であり将来を保証しません。"


def sidebar_controls(presets: Dict[str, Dict[str, str]]) -> Tuple[str, str, str, Dict[str, str], Tuple[int, int], bool]:
    """Render sidebar controls and return user selections."""

    st.sidebar.header("分析条件")
    industry = st.sidebar.text_input("業種（フリーワード）", "美容室")
    prefecture = st.sidebar.selectbox(
        "地域（都道府県）",
        [
            "全国",
            "北海道",
            "青森県",
            "岩手県",
            "宮城県",
            "秋田県",
            "山形県",
            "福島県",
            "茨城県",
            "栃木県",
            "群馬県",
            "埼玉県",
            "千葉県",
            "東京都",
            "神奈川県",
            "新潟県",
            "富山県",
            "石川県",
            "福井県",
            "山梨県",
            "長野県",
            "岐阜県",
            "静岡県",
            "愛知県",
            "三重県",
            "滋賀県",
            "京都府",
            "大阪府",
            "兵庫県",
            "奈良県",
            "和歌山県",
            "鳥取県",
            "島根県",
            "岡山県",
            "広島県",
            "山口県",
            "徳島県",
            "香川県",
            "愛媛県",
            "高知県",
            "福岡県",
            "佐賀県",
            "長崎県",
            "熊本県",
            "大分県",
            "宮崎県",
            "鹿児島県",
            "沖縄県",
        ],
        index=41,
    )
    preset_key = st.sidebar.selectbox(
        "統計表プリセット",
        list(presets.keys()),
        format_func=lambda key: presets[key]["name"],
    )
    period = st.sidebar.slider("期間（年）", 2009, 2023, (2012, 2021))
    nowcast = st.sidebar.toggle("Nowcast推定を表示", value=True)
    advanced = st.sidebar.expander("高度な設定")
    with advanced:
        st.caption("sample_queries.json を編集することで統計表を追加できます。")
        st.json(presets[preset_key])
    st.sidebar.markdown("---")
    st.sidebar.caption(FOOTER_TEXT)
    return industry, prefecture, preset_key, presets[preset_key], period, nowcast


def footer() -> None:
    """Render footer text."""

    st.markdown(f"<div style='font-size:0.8rem;color:#555;margin-top:2rem;'>{FOOTER_TEXT}</div>", unsafe_allow_html=True)

