"""
news_fetcher.py
主要メディアの公式RSSフィードから客観的なニュースを取得・整形するモジュール
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

# 日本標準時 (JST)
JST = timezone(timedelta(hours=9))

# カテゴリ別RSSフィード一覧の定義
# 個人プロファイル・推薦アルゴリズムを一切含まない公的・主要報道機関のトップフィード
RSS_SOURCES: Dict[str, List[Dict[str, str]]] = {
    "総合・主要": [
        {
            "media": "NHKニュース",
            "category": "主要ニュース",
            "url": "https://www.nhk.or.jp/rss/news/cat0.xml",
            "badge_color": "#005BAC",
        },
        {
            "media": "Yahoo!ニュース",
            "category": "主要トピックス",
            "url": "https://news.yahoo.co.jp/rss/topics/top-picks.xml",
            "badge_color": "#FF0033",
        },
        {
            "media": "BBCニュース",
            "category": "トップニュース",
            "url": "https://feeds.bbci.co.uk/japanese/rss.xml",
            "badge_color": "#B80000",
        },
    ],
    "社会・国内": [
        {
            "media": "NHKニュース",
            "category": "社会",
            "url": "https://www.nhk.or.jp/rss/news/cat1.xml",
            "badge_color": "#005BAC",
        },
        {
            "media": "Yahoo!ニュース",
            "category": "国内",
            "url": "https://news.yahoo.co.jp/rss/topics/domestic.xml",
            "badge_color": "#FF0033",
        },
    ],
    "国際": [
        {
            "media": "NHKニュース",
            "category": "国際",
            "url": "https://www.nhk.or.jp/rss/news/cat6.xml",
            "badge_color": "#005BAC",
        },
        {
            "media": "Yahoo!ニュース",
            "category": "国際",
            "url": "https://news.yahoo.co.jp/rss/topics/world.xml",
            "badge_color": "#FF0033",
        },
        {
            "media": "BBCニュース",
            "category": "国際",
            "url": "https://feeds.bbci.co.uk/japanese/rss.xml",
            "badge_color": "#B80000",
        },
    ],
    "経済": [
        {
            "media": "NHKニュース",
            "category": "経済",
            "url": "https://www.nhk.or.jp/rss/news/cat5.xml",
            "badge_color": "#005BAC",
        },
        {
            "media": "Yahoo!ニュース",
            "category": "経済",
            "url": "https://news.yahoo.co.jp/rss/topics/business.xml",
            "badge_color": "#FF0033",
        },
    ],
    "科学・IT": [
        {
            "media": "NHKニュース",
            "category": "科学・文化",
            "url": "https://www.nhk.or.jp/rss/news/cat3.xml",
            "badge_color": "#005BAC",
        },
        {
            "media": "Yahoo!ニュース",
            "category": "IT・科学",
            "url": "https://news.yahoo.co.jp/rss/topics/it.xml",
            "badge_color": "#FF0033",
        },
    ],
}


def clean_html(raw_html: str) -> str:
    """HTMLタグを除去し、プレーンテキストを抽出する"""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    # 不要な改行や連続スペースを正規化
    return " ".join(text.split())


def parse_published_date(entry: Any) -> Optional[datetime]:
    """エントリから日時を抽出し、JSTのdatetimeオブジェクトとして返す"""
    raw_date = None
    if hasattr(entry, "published"):
        raw_date = entry.published
    elif hasattr(entry, "updated"):
        raw_date = entry.updated
    elif hasattr(entry, "created"):
        raw_date = entry.created

    if not raw_date:
        return None

    try:
        dt = date_parser.parse(raw_date)
        if dt.tzinfo is None:
            # タイムゾーン情報がない場合はJSTとみなす
            dt = dt.replace(tzinfo=JST)
        else:
            # JSTに変換
            dt = dt.astimezone(JST)
        return dt
    except Exception:
        return None


def format_relative_time(dt: Optional[datetime]) -> str:
    """日時を人間が読みやすい形式（'XX分前', 'XX時間前', または日付）にフォーマット"""
    if not dt:
        return "日時不明"

    now = datetime.now(JST)
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 0:
        # 未来の日時が設定されている等の場合
        return dt.strftime("%Y/%m/%d %H:%M")
    elif seconds < 60:
        return f"{seconds}秒前"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分前"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours}時間前"
    elif seconds < 86400 * 3:
        days = seconds // 86400
        return f"{days}日前"
    else:
        return dt.strftime("%Y/%m/%d %H:%M")


def fetch_category_news(category: str) -> List[Dict[str, Any]]:
    """指定されたカテゴリのRSSフィードを取得・統合・ソートして返す"""
    sources = RSS_SOURCES.get(category, [])
    articles: List[Dict[str, Any]] = []
    seen_titles = set()

    for source in sources:
        try:
            feed = feedparser.parse(
                source["url"],
                agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            for entry in feed.entries:
                title = clean_html(getattr(entry, "title", "")).strip()
                if not title or title in seen_titles:
                    continue

                seen_titles.add(title)
                link = getattr(entry, "link", "")
                
                # 概要取得 (summary, description, contentなど)
                summary_raw = getattr(entry, "summary", "") or getattr(entry, "description", "")
                summary = clean_html(summary_raw)
                
                # summaryがタイトルと同一または空の場合は補正
                if summary == title:
                    summary = ""

                dt = parse_published_date(entry)
                relative_time = format_relative_time(dt)
                formatted_dt = dt.strftime("%Y/%m/%d %H:%M") if dt else "日時不明"

                articles.append({
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "media": source["media"],
                    "media_category": source["category"],
                    "badge_color": source["badge_color"],
                    "published_dt": dt,
                    "published_str": formatted_dt,
                    "relative_time": relative_time,
                })
        except Exception as e:
            print(f"Error fetching {source['media']} ({source['url']}): {e}")

    # 公開日時の新しい順にソート（日時不明は末尾）
    articles.sort(
        key=lambda x: x["published_dt"] if x["published_dt"] is not None else datetime.min.replace(tzinfo=JST),
        reverse=True,
    )

    return articles
