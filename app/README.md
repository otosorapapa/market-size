# 自動市場分析ダッシュボード

Streamlit ベースで業種・地域を入力すると、e-Stat API から統計データを取得し、Nowcast 推計および OpenAI を活用した分析レポートを生成する最小実装です。

## セットアップ

1. リポジトリをクローンし、依存パッケージをインストールします。

   ```bash
   cd app
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. `.streamlit/secrets.toml` に API キーを設定します。環境変数 `ESTAT_APP_ID` に設定しても読み込まれます。

   ```toml
   ESTAT_APP_ID = "あなたのe-StatアプリID"
   OPENAI_API_KEY = "あなたのOpenAI APIキー"
   OPENAI_MODEL = "gpt-4o-mini"
   ```

3. アプリを起動します。

   ```bash
   streamlit run streamlit_app.py
   ```

## 使い方

1. サイドバーで業種名（フリーワード）と都道府県、統計表プリセット、期間、Nowcast オプションを選択します。
2. 「分析する」ボタンをクリックすると、e-Stat から統計を取得し、グラフや KPI がダッシュボードに表示されます。
3. レポートタブでは PEST/3C/5 Forces 分析と審査員向け 1 枚サマリーを生成します。
4. エクスポートタブから PDF / PPTX / Excel をダウンロードできます。

## 拡張ポイント

- `data/sample_queries.json` に統計表 ID やパラメータを追加して用途に応じて拡張できます。
- `services/jsic_mapper.py` の辞書を更新すると、業種の補完精度を高められます。
- `services/nowcast.py` では月次成長率を渡すことで Nowcast の計算を高度化できます。
- `services/llm_writer.py` のプロンプトを調整し、生成する文章の粒度やトーンをカスタマイズできます。

## 注意事項

- e-Stat API の呼び出しにはアプリケーション ID が必要です。利用規約および二次利用ポリシーに従ってください。
- Nowcast の推定値は参考値であり、将来の業績を保証するものではありません。
- OpenAI API の利用に伴うコストと利用規約に留意してください。

