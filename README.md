# 客観的・主要ニュースダッシュボード (Neutral News)

個人へのパーソナライズを一切行わず、客観的な「世の中の今日の主要ニュース」を一覧・要約して確認できるStreamlitダッシュボードWebアプリケーションです。

---

## 🌟 特徴
1. **完全ノー・パーソナライズ**:
   - 閲覧履歴やCookie、個人の嗜好プロファイルに基づく推薦アルゴリズムを一切排除。
   - 公共放送（NHK）、主要ポータル（Yahoo!ニュース主要トピックス）、国際報道（BBC）のトップニュースRSSフィードから直接取得しています。
2. **カテゴリ別タブ切り替え**:
   - 総合・主要、社会・国内、国際、経済、科学・ITのタブでスピーディに閲覧。
3. **直感的なダッシュボードUI**:
   - 記事タイトル、概要（サマリー）、配信元メディアバッジ、掲載日時（相対時間＋JST）、元記事へのリンクを整理したカードデザイン。
4. **最新情報への手動更新**:
   - サイドバーの「🔄 最新情報を再取得」ボタンでキャッシュを即座に破棄して最新データを取得可能。
5. **絞り込み・検索機能**:
   - キーワードによるリアルタイム検索
   - 特定メディアのみ（NHK / Yahoo! / BBC）への絞り込み表示
   - 表示件数の変更スライダー

---

## 🚀 起動方法

### ご利用の仮想環境 (`.default_env`) で起動する場合
すでに必要なライブラリはインストール済みです。ターミナルで以下のコマンドを実行してください。

```powershell
streamlit run app.py
```

※ もし `streamlit` コマンドが認識されない場合は、仮想環境のフルパスを指定して実行できます：
```powershell
C:\Users\kazu0\.default_env\Scripts\streamlit.exe run app.py
```

実行後、自動的にブラウザで `http://localhost:8501` が開きます。

---

## 📁 ファイル構成
- `app.py`: Streamlitアプリケーション本体（UI設計、カード表示、フィルタ処理）
- `news_fetcher.py`: RSSフィードの取得・解析・HTMLクレンジング・日時正規化ロジック
- `requirements.txt`: 依存Pythonライブラリ一覧（Streamlit Cloudで自動読み込み）
- `.gitignore`: Git管理除外設定
- `README.md`: 本説明書

---

## ☁️ Streamlit Community Cloud へのデプロイ手順

1. **GitHubに新しいリポジトリを作成**（例: `neutral-news-dashboard`）
2. **ローカルリポジトリをGitHubにプッシュ**:
   ```bash
   git remote add origin https://github.com/<あなたのユーザー名>/<リポジトリ名>.git
   git push -u origin main
   ```
3. **Streamlit Community Cloudにログイン**:
   - [share.streamlit.io](https://share.streamlit.io/) にアクセスし、GitHubアカウントでログイン
4. **新規アプリの作成 (New app)**:
   - **Repository**: 作成したリポジトリを選択
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **Deploy!** ボタンをクリック

