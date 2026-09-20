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
    "株": [
        {
            "media": "株式・市場ニュース",
            "category": "株価・市況",
            "url": "https://news.google.com/rss/search?q=%E6%A0%AA%E4%BE%A1+OR+%E6%97%A5%E7%B5%8C%E5%B9%B3%E5%9D%87+OR+%E6%A0%AA%E5%BC%8F%E5%B8%82%E5%A0%B4+OR+%E6%97%A5%E6%9C%AC%E6%A0%AA+OR+%E7%B1%B3%E5%9B%BD%E6%A0%AA&hl=ja&gl=JP&ceid=JP:ja",
            "badge_color": "#00897B",
            "is_google_news": True,
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
    "Esports": [
        {
            "media": "4Gamer.net",
            "category": "ゲーム・eスポーツ",
            "url": "https://www.4gamer.net/rss/index.xml",
            "badge_color": "#E65100",
        },
        {
            "media": "eスポーツ総合",
            "category": "eスポーツ",
            "url": "https://news.google.com/rss/search?q=e%E3%82%B9%E3%83%9D%E3%83%BC%E3%83%84&hl=ja&gl=JP&ceid=JP:ja",
            "badge_color": "#2E7D32",
            "is_google_news": True,
        },
    ],
    "天気": [
        {
            "media": "気象・天気情報",
            "category": "天気・防災",
            "url": "https://news.google.com/rss/search?q=%E5%A4%A9%E6%B0%97+OR+%E6%B0%97%E8%B1%A1&hl=ja&gl=JP&ceid=JP:ja",
            "badge_color": "#0288D1",
            "is_google_news": True,
        },
    ],
    "猫": [
        {
            "media": "猫ジャーナル",
            "category": "猫トピックス",
            "url": "https://nekojournal.net/?feed=rss2",
            "badge_color": "#D81B60",
        },
        {
            "media": "猫ニュース総合",
            "category": "猫ニュース",
            "url": "https://news.google.com/rss/search?q=%E7%8C%AB&hl=ja&gl=JP&ceid=JP:ja",
            "badge_color": "#FB8C00",
            "is_google_news": True,
        },
    ],
}


def clean_html(raw_html: str) -> str:
    """HTMLタグを除去し、プレーンテキストを抽出する"""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
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
            dt = dt.replace(tzinfo=JST)
        else:
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

            is_google = source.get("is_google_news", False)

            for entry in feed.entries:
                title = clean_html(getattr(entry, "title", "")).strip()
                if not title:
                    continue

                media_name = source["media"]
                # Google Newsの場合は元メディア名を抽出
                if is_google:
                    src = getattr(entry, "source", None)
                    if src and isinstance(src, dict) and src.get("title"):
                        media_name = src.get("title")
                    elif src and hasattr(src, "title") and src.title:
                        media_name = src.title
                    
                    # 末尾の " - メディア名" をタイトルからカット
                    if media_name and title.endswith(f" - {media_name}"):
                        title = title[:-len(f" - {media_name}")].strip()

                if title in seen_titles:
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
                    "media": media_name,
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
