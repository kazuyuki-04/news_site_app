import streamlit as st
from datetime import datetime, timezone, timedelta
import html
from news_fetcher import RSS_SOURCES, fetch_category_news, JST

# ページ基本設定
st.set_page_config(
    page_title="Neutral News | 客観的主要ニュース",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# カテゴリのアイコン定義
CATEGORY_ICONS = {
    "総合・主要": "📌",
    "社会・国内": "🏛️",
    "国際": "🌍",
    "経済": "📈",
    "株": "📊",
    "科学・IT": "🔬",
    "Esports": "🎮",
    "天気": "☀️",
    "猫": "🐱",
}

categories = list(RSS_SOURCES.keys())

# セッション状態の初期化
if "selected_category" not in st.session_state:
    st.session_state.selected_category = categories[0]

# カスタムCSS（見やすいカードUI、バッジ、フローティング上へ戻るボタン等）
st.markdown(
    """
    <style>
    .main-header {
        margin-bottom: 0.3rem;
    }
    .sub-text {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1.2rem;
    }
    .news-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .card-meta {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 0.82rem;
        margin-bottom: 0.4rem;
        flex-wrap: wrap;
    }
    .media-badge {
        color: #ffffff;
        padding: 0.18rem 0.55rem;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 0.02em;
    }
    .time-badge {
        color: #777;
        font-size: 0.8rem;
    }
    .news-title {
        font-size: 1.15rem;
        font-weight: 700;
        line-height: 1.45;
        margin: 0.3rem 0 0.5rem 0;
    }
    .news-title a {
        text-decoration: none;
        color: inherit;
    }
    .news-title a:hover {
        text-decoration: underline;
        color: #1a73e8;
    }
    .news-summary {
        font-size: 0.92rem;
        line-height: 1.55;
        color: var(--text-color);
        opacity: 0.88;
        margin-bottom: 0.6rem;
    }
    .news-footer {
        display: flex;
        justify-content: flex-end;
        font-size: 0.85rem;
    }
    .link-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        color: #1a73e8;
        text-decoration: none;
        font-weight: 500;
    }
    .link-btn:hover {
        text-decoration: underline;
    }
    /* 画面右下に固定される小さな「上へ戻る」ボタン */
    .floating-top-btn {
        position: fixed;
        bottom: 24px;
        right: 24px;
        background-color: rgba(26, 115, 232, 0.9);
        color: #ffffff !important;
        padding: 7px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-decoration: none !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25);
        z-index: 999999;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        cursor: pointer;
        backdrop-filter: blur(4px);
        transition: transform 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
    }
    .floating-top-btn:hover {
        background-color: #1557b0;
        transform: translateY(-2px);
        box-shadow: 0 5px 14px rgba(0, 0, 0, 0.35);
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# キャッシュ付きデータ取得関数 (有効期限10分)
@st.cache_data(ttl=600, show_spinner=False)
def get_cached_news(category: str):
    return fetch_category_news(category)


# サイドバー（設定・フィルタ・カテゴリ切り替え・ポリシー）
with st.sidebar:
    st.title("⚙️ 設定 & フィルタ")

    st.markdown("### 🔄 データの更新")
    if st.button("🔄 最新情報を再取得", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.success("キャッシュをクリアして再取得しました！")
        st.rerun()

    now_jst = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
    st.caption(f"最終表示時刻: {now_jst} (JST)")

    st.divider()

    st.markdown("### 🔍 検索・絞り込み")
    search_keyword = st.text_input("キーワード検索", placeholder="例: 日経平均、大会、台風、子猫、AI...")

    # 表示件数
    page_limit = st.slider("表示件数", min_value=10, max_value=100, value=30, step=10)

    st.divider()

    # ★ サイドバーからのカテゴリ切り替えボタン（スクロール時もここから遷移可能）
    st.markdown("### 📑 カテゴリ切り替え")
    st.caption("下へスクロール中もここから瞬時に切り替えできます")
    for cat in categories:
        is_active = (st.session_state.selected_category == cat)
        if st.button(
            f"{CATEGORY_ICONS.get(cat, '📌')} {cat}",
            key=f"sidebar_btn_{cat}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.selected_category = cat
            if "category_pill_selector" in st.session_state:
                st.session_state.category_pill_selector = cat
            st.rerun()

    st.divider()

    st.markdown(
        """
        ### ⚖️ 本サイトのポリシー
        - **完全ノー・パーソナライズ**: 閲覧履歴、クッキー、個人の嗜好による推薦アルゴリズムは一切排除。
        - **客観的・中立的集約**: 公共放送・主要報道機関・専門ポータルのフィードから直接取得。
        - **エコーチェンバー防止**: 関心領域に偏らず、いま起きている事実や関心トピックをフラットに確認できます。
        """
    )


# ページ先頭のアンカー
st.markdown('<div id="top-anchor"></div>', unsafe_allow_html=True)

# 画面右下のフローティング「上へ戻る」ボタン
st.markdown(
    """
    <a href="#top-anchor" class="floating-top-btn" title="ページ最上部へ戻る" onclick="
        const main = window.parent.document.querySelector('section.main') || window.parent.document.querySelector('.main') || window;
        if (main && main.scrollTo) {
            main.scrollTo({top: 0, behavior: 'smooth'});
        }
    ">
        ⬆ 上へ
    </a>
    """,
    unsafe_allow_html=True,
)

# メインヘッダー
st.markdown("<h1 class='main-header'>🌐 客観的・主要ニュースダッシュボード</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='sub-text'>個人の好みに合わせたパーソナライズを行わず、公的・主要メディアのトップニュースを中立的に一覧できます。</p>",
    unsafe_allow_html=True,
)

# 上部のカテゴリ選択ピル
def on_pill_change():
    if st.session_state.category_pill_selector:
        st.session_state.selected_category = st.session_state.category_pill_selector

pill_selection = st.pills(
    "カテゴリ選択",
    categories,
    format_func=lambda cat: f"{CATEGORY_ICONS.get(cat, '📌')} {cat}",
    selection_mode="single",
    default=st.session_state.selected_category,
    key="category_pill_selector",
    on_change=on_pill_change,
    label_visibility="collapsed",
)

# ピルの値が未同期の場合に同期
current_category = st.session_state.selected_category
if pill_selection and pill_selection != current_category:
    st.session_state.selected_category = pill_selection
    current_category = pill_selection

# カテゴリのニュース取得
with st.spinner(f"「{current_category}」の最新ニュースを取得中..."):
    articles = get_cached_news(current_category)

filtered = articles

# キーワードフィルタ
if search_keyword.strip():
    kw = search_keyword.strip().lower()
    filtered = [
        a for a in filtered
        if kw in a["title"].lower() or kw in a["summary"].lower() or kw in a["media"].lower()
    ]

# 該当件数表示
col_meta, _ = st.columns([2, 1])
with col_meta:
    st.caption(f"現在のカテゴリ: **{CATEGORY_ICONS.get(current_category, '📌')} {current_category}** ｜ 該当記事: **{len(filtered)}** 件 （全 {len(articles)} 件中）")

if not filtered:
    st.info("条件に一致するニュースが見つかりませんでした。別のキーワードをお試しください。")
else:
    # 記事一覧表示 (カードレンダリング)
    for item in filtered[:page_limit]:
        title_escaped = html.escape(item["title"])
        summary_escaped = html.escape(item["summary"]) if item["summary"] else ""
        link_escaped = html.escape(item["link"])
        media_escaped = html.escape(item["media"])
        badge_color = item.get("badge_color", "#1a73e8")
        time_str = f"{item['relative_time']} ({item['published_str']})"

        summary_html = (
            f"<div class='news-summary'>{summary_escaped}</div>"
            if summary_escaped
            else ""
        )

        card_html = f"""
        <div class="news-card">
            <div class="card-meta">
                <span class="media-badge" style="background-color: {badge_color};">{media_escaped}</span>
                <span class="time-badge">🕒 {time_str}</span>
            </div>
            <div class="news-title">
                <a href="{link_escaped}" target="_blank" rel="noopener noreferrer">{title_escaped}</a>
            </div>
            {summary_html}
            <div class="news-footer">
                <a class="link-btn" href="{link_escaped}" target="_blank" rel="noopener noreferrer">
                    元記事を読む ↗
                </a>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    # 一番下にスクロールしたときの上に戻るボタン
    st.markdown(
        """
        <div style="text-align: center; margin: 2.5rem 0 2rem 0;">
            <a href="#top-anchor" style="
                display: inline-flex;
                align-items: center;
                gap: 6px;
                color: #1a73e8;
                font-size: 0.85rem;
                font-weight: 500;
                text-decoration: none;
                padding: 7px 18px;
                border: 1px solid rgba(26, 115, 232, 0.35);
                border-radius: 20px;
                background-color: rgba(26, 115, 232, 0.05);
                transition: all 0.2s ease;
            " onclick="
                const main = window.parent.document.querySelector('section.main') || window.parent.document.querySelector('.main') || window;
                if (main && main.scrollTo) {
                    main.scrollTo({top: 0, behavior: 'smooth'});
                }
            ">
                ⬆ ページ上部へ戻る
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
