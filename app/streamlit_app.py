"""Streamlit application for automated market analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from components import charts, layout
from services import exporters, jsic_mapper, llm_writer, nowcast
from services.estat_client import EstatClient

DATA_DIR = Path(__file__).parent / "data"


@st.cache_resource
def load_presets() -> Dict[str, Dict[str, str]]:
    with open(DATA_DIR / "sample_queries.json", "r", encoding="utf-8") as file:
        return json.load(file)


def _load_estat_client() -> EstatClient:
    if "ESTAT_APP_ID" not in st.secrets:
        raise RuntimeError("ESTAT_APP_ID が secrets.toml に設定されていません。")
    return EstatClient(st.secrets["ESTAT_APP_ID"])


def _prepare_parameters(meta: Dict[str, str], period: Tuple[int, int], prefecture_code: str) -> Dict[str, str]:
    params = dict(meta.get("default_params", {}))
    params["time"] = f"{period[0]}-{period[1]}"
    if prefecture_code:
        params["cdArea"] = prefecture_code
    return params


AREA_CODES = {
    "全国": "00000",
    "北海道": "01",
    "青森県": "02",
    "岩手県": "03",
    "宮城県": "04",
    "秋田県": "05",
    "山形県": "06",
    "福島県": "07",
    "茨城県": "08",
    "栃木県": "09",
    "群馬県": "10",
    "埼玉県": "11",
    "千葉県": "12",
    "東京都": "13",
    "神奈川県": "14",
    "新潟県": "15",
    "富山県": "16",
    "石川県": "17",
    "福井県": "18",
    "山梨県": "19",
    "長野県": "20",
    "岐阜県": "21",
    "静岡県": "22",
    "愛知県": "23",
    "三重県": "24",
    "滋賀県": "25",
    "京都府": "26",
    "大阪府": "27",
    "兵庫県": "28",
    "奈良県": "29",
    "和歌山県": "30",
    "鳥取県": "31",
    "島根県": "32",
    "岡山県": "33",
    "広島県": "34",
    "山口県": "35",
    "徳島県": "36",
    "香川県": "37",
    "愛媛県": "38",
    "高知県": "39",
    "福岡県": "40",
    "佐賀県": "41",
    "長崎県": "42",
    "熊本県": "43",
    "大分県": "44",
    "宮崎県": "45",
    "鹿児島県": "46",
    "沖縄県": "47",
}


def _create_placeholder(period: Tuple[int, int]) -> pd.DataFrame:
    years = list(range(period[0], period[1] + 1))
    values = np.linspace(18000, 25000, len(years))
    return pd.DataFrame({"time": years, "value": values})


def _calculate_kpis(series: pd.Series) -> Dict[str, float]:
    series = series.dropna()
    latest_year = series.index.max()
    latest_value = series.loc[latest_year]
    previous_value = series.loc[latest_year - 1] if latest_year - 1 in series.index else np.nan
    yoy = (latest_value - previous_value) / previous_value if previous_value and not np.isnan(previous_value) else np.nan
    start_year = series.index.min()
    years = latest_year - start_year if latest_year != start_year else 1
    cagr = (latest_value / series.loc[start_year]) ** (1 / years) - 1 if series.loc[start_year] else np.nan
    return {
        "latest_year": latest_year,
        "latest_value": float(latest_value),
        "yoy": float(yoy) if not np.isnan(yoy) else np.nan,
        "cagr": float(cagr) if not np.isnan(cagr) else np.nan,
    }


def main() -> None:
    st.set_page_config(page_title="自動市場分析ダッシュボード", layout="wide")
    st.title("自動市場分析ダッシュボード")
    st.caption("業種と地域を選ぶだけで、e-Stat統計と生成AIを組み合わせたレポートを自動生成します。")

    presets = load_presets()
    industry, prefecture, preset_key, preset_meta, period, use_nowcast = layout.sidebar_controls(presets)

    suggestions = jsic_mapper.guess_jsic(industry)
    with st.expander("JSIC候補を見る", expanded=False):
        if suggestions:
            for item in suggestions:
                st.write(f"{item['label']} (JSIC {item['jsic_code']}) - 類似度 {item['score']:.2f}")
        else:
            st.write("候補が見つかりませんでした。")

    if "run_analysis" not in st.session_state:
        st.session_state["run_analysis"] = False
    if st.sidebar.button("分析する", type="primary"):
        st.session_state["run_analysis"] = True

    if not st.session_state["run_analysis"]:
        layout.footer()
        return

    prefecture_code = AREA_CODES.get(prefecture, "00000")
    params = _prepare_parameters(preset_meta, period, prefecture_code)

    try:
        client = _load_estat_client()
    except RuntimeError as error:
        st.error(str(error))
        data = _create_placeholder(period)
        st.info("シークレット未設定のためサンプルデータを使用しています。")
    else:
        try:
            with st.status("e-Statから統計を取得中", expanded=True):
                data = client.get(preset_meta["statsDataId"], params)
        except Exception as exc:  # pragma: no cover - defensive against API issues
            st.warning(f"統計取得でエラーが発生しました: {exc}. サンプルデータを表示します。")
            data = _create_placeholder(period)

    if data.empty:
        data = _create_placeholder(period)

    if not pd.api.types.is_numeric_dtype(data["value"]):
        data["value"] = pd.to_numeric(data["value"], errors="coerce")
    if not pd.api.types.is_numeric_dtype(data["time"]):
        data["time"] = data["time"].astype(str).str.extract(r"(\d{4})").astype(float)
    data = data.dropna(subset=["time", "value"])
    data["time"] = data["time"].astype(int)

    annual_series = data.groupby("time")["value"].sum().sort_index()
    annual_series.name = "市場規模"

    if use_nowcast:
        monthly_growth = pd.Series(dtype=float)
        adjusted_series = nowcast.apply_nowcast(annual_series, monthly_growth)
    else:
        adjusted_series = annual_series

    kpis = _calculate_kpis(adjusted_series)

    tab_dashboard, tab_report, tab_export = st.tabs(["ダッシュボード", "レポート", "エクスポート"])

    with tab_dashboard:
        cols = st.columns(3)
        cols[0].metric("最新市場規模 (万円)", f"{kpis['latest_value']:,.0f}", delta=f"{kpis['yoy']*100:.1f}%" if not np.isnan(kpis["yoy"]) else "-" )
        cols[1].metric("最新年", int(kpis["latest_year"]))
        cols[2].metric("CAGR", f"{kpis['cagr']*100:.1f}%" if not np.isnan(kpis["cagr"]) else "-")

        chart_df = adjusted_series.reset_index().rename(columns={"time": "年", "value": "市場規模"})
        time_fig = charts.time_series(chart_df, x="年", y="市場規模", title="市場規模の推移", unit="万円")
        st.plotly_chart(time_fig, use_container_width=True)

        density_df = pd.DataFrame(
            {
                "地域": [prefecture],
                "人口1万人当たり事業所数": [round(kpis["latest_value"] / 10000, 2)],
                "市場規模": [kpis["latest_value"]],
            }
        )
        scatter_fig = charts.scatter_density(
            density_df,
            x="人口1万人当たり事業所数",
            y="市場規模",
            text="地域",
            title="競合密度（人口1万人当たり）",
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

    with tab_report:
        context = {
            "業種": industry,
            "地域": prefecture,
            "最新市場規模": f"{kpis['latest_year']}年 {kpis['latest_value']:,.0f} 万円",
            "前年比": f"{kpis['yoy']*100:.1f}%" if not np.isnan(kpis["yoy"]) else "データ不足",
            "CAGR": f"{kpis['cagr']*100:.1f}%" if not np.isnan(kpis["cagr"]) else "データ不足",
            "出典": "政府統計の総合窓口（e-Stat）",
        }
        try:
            sections = llm_writer.generate_sections(context)
        except Exception as exc:  # pragma: no cover - external dependency
            st.warning(f"OpenAIによるレポート生成でエラーが発生しました: {exc}")
            sections = {key: "生成に失敗しました。" for key in ["pest", "threec", "fiveforces", "summary1pager"]}
        st.subheader("PEST分析")
        st.markdown(sections["pest"])
        st.subheader("5 Forces分析")
        st.markdown(sections["fiveforces"])
        st.subheader("3C分析")
        st.markdown(sections["threec"])
        st.subheader("審査員向け1枚サマリー")
        st.markdown(sections["summary1pager"])
        st.caption("レポートのフレームワーク（PEST/3C/5Forces）は小規模事業者の意思決定支援用テンプレに基づき自動整形。")

    with tab_export:
        st.write("取得したデータとレポートを各形式でダウンロードできます。")
        figures_png = charts.figures_to_png([time_fig, scatter_fig])
        highlights = {
            "市場規模": f"{kpis['latest_year']}年 {kpis['latest_value']:,.0f} 万円",
            "前年比": context["前年比"],
            "CAGR": context["CAGR"],
        }
        title = f"{industry}_{prefecture}市場分析"
        pdf_bytes = exporters.to_pdf(sections["summary1pager"], [chart_df], title=title)
        pptx_bytes = exporters.to_pptx(figures_png, highlights, title=title)
        excel_bytes = exporters.to_excel({"raw": data.reset_index(drop=True), "annual": chart_df})

        st.download_button(
            label="PDFダウンロード",
            data=pdf_bytes,
            file_name=exporters.filename(f"{industry}_{prefecture}", "pdf"),
            mime="application/pdf",
        )
        st.download_button(
            label="PPTXダウンロード",
            data=pptx_bytes,
            file_name=exporters.filename(f"{industry}_{prefecture}", "pptx"),
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        st.download_button(
            label="Excelダウンロード",
            data=excel_bytes,
            file_name=exporters.filename(f"{industry}_{prefecture}", "xlsx"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    layout.footer()


if __name__ == "__main__":
    main()

