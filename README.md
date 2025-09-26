# Market Size Dashboard

このリポジトリは、Streamlit を用いた自動市場分析アプリのサンプル実装です。詳細な利用方法やセットアップ手順は `app/README.md` を参照してください。

## ディレクトリ構成

- `app/` – Streamlit アプリ本体およびサービス・コンポーネントモジュール
- `app/data/` – JSIC 辞書や統計プリセットのサンプルデータ
- `app/services/` – e-Stat API クライアントや Nowcast、OpenAI 連携、エクスポート機能
- `app/components/` – グラフ生成や UI レイアウト共通部品

## 起動方法

```bash
cd app
pip install -r requirements.txt
streamlit run streamlit_app.py
```

OpenAI と e-Stat の API キーは `app/.streamlit/secrets.toml` に設定してください。

