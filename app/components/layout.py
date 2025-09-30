"""Layout helpers for the Streamlit dashboard."""

from __future__ import annotations

from typing import Dict

import streamlit as st


FOOTER_TEXT = "統計出典：政府統計の総合窓口（e-Stat）。二次利用ポリシー遵守。 / 年次統計の最新値推定（Nowcast）は月次指標による近似。参考値であり将来を保証しません。"


def sidebar_controls(
    presets: Dict[str, Dict[str, str]],
    *,
    on_submit,
) -> None:
    """Render sidebar controls and delegate submission to a callback."""

    st.sidebar.header("分析条件")
    prefecture_options = [
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
    ]

    if st.session_state["_prefecture_widget"] not in prefecture_options:
        st.session_state["_prefecture_widget"] = prefecture_options[0]

    with st.sidebar.form("analysis_controls"):
        st.text_input(
            "業種（フリーワード）",
            value=st.session_state["_industry_widget"],
            key="_industry_widget",
        )
        st.selectbox(
            "地域（都道府県）",
            prefecture_options,
            index=prefecture_options.index(st.session_state["_prefecture_widget"]),
            key="_prefecture_widget",
        )
        preset_keys = list(presets.keys())
        if st.session_state["_preset_widget"] not in presets:
            st.session_state["_preset_widget"] = preset_keys[0]
        st.selectbox(
            "統計表プリセット",
            preset_keys,
            format_func=lambda key: presets[key]["name"],
            index=preset_keys.index(st.session_state["_preset_widget"]),
            key="_preset_widget",
        )
        st.slider(
            "期間（年）",
            2009,
            2023,
            value=st.session_state["_period_widget"],
            key="_period_widget",
        )
        st.toggle(
            "Nowcast推定を表示",
            value=st.session_state["_nowcast_widget"],
            key="_nowcast_widget",
        )
        st.text_input(
            "e-Stat APIキー",
            value=st.session_state["_estat_api_key_widget"],
            key="_estat_api_key_widget",
            type="password",
            help="e-StatのアプリケーションIDを入力してください。",
        )
        st.form_submit_button("分析する", type="primary", on_click=on_submit)

    advanced = st.sidebar.expander("高度な設定")
    with advanced:
        st.caption("sample_queries.json を編集することで統計表を追加できます。")
        preview_preset_key = st.session_state.get("_preset_widget", st.session_state.get("preset_key"))
        if preview_preset_key not in presets:
            preview_preset_key = list(presets.keys())[0]
        stats_id = presets[preview_preset_key].get("statsDataId") or "未設定"
        st.text_input("statsDataId", value=str(stats_id), disabled=True)
        st.json(presets[preview_preset_key])
    st.sidebar.markdown("---")
    st.sidebar.caption(FOOTER_TEXT)


def footer() -> None:
    """Render footer text."""

    st.markdown(f"<div style='font-size:0.8rem;color:#555;margin-top:2rem;'>{FOOTER_TEXT}</div>", unsafe_allow_html=True)

