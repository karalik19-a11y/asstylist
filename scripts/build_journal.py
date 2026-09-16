#!/usr/bin/env python3
"""Build ASStylist's weekly fashion magazine from public RSS/search feeds.

No paid API, SDK, key, database or AI provider is required. The script uses
public Google News RSS topic queries plus deterministic editorial scoring.
Publisher-selected images are cached into the static site, while article
briefs are assembled from the publisher's public RSS/meta descriptions.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path("frontend/public/journal.json")
IMAGE_DIR = Path("frontend/public/journal-images")
USER_AGENT = "ASStylist-Journal/2.0 (+https://github.com/karalik19-a11y/asstylist)"

FEEDS = [
    ("world", "fashion industry news runway designers brands", "Мир моды"),
    ("russian-streetwear", "российский streetwear мода бренды стритвир", "Русский streetwear"),
    ("runway", "fashion week runway shows collection", "Показы"),
    ("merch", "fashion merch drop collaboration capsule collection", "Мерчи"),
    ("social-trends", "TikTok fashion trend", "TikTok"),
    ("social-trends", "Instagram fashion trend streetwear", "Instagram"),
    ("social-trends", "Pinterest fashion trend aesthetic", "Pinterest"),
    ("social-trends", "streetwear trend Gen Z fashion social media", "Соцсети"),
]

TRUST = {
    "Vogue": 1.0, "WWD": 1.0, "Hypebeast": 0.95, "Highsnobiety": 0.95,
    "GQ": 0.9, "Esquire": 0.9, "The Business of Fashion": 1.0,
    "Dazed": 0.95, "i-D": 0.9, "Complex": 0.9, "FashionUnited": 0.9,
    "The Cut": 0.9, "Who What Wear": 0.8, "SNEAKERS": 0.8,
}
KEYWORDS = [
    "drop", "collaboration", "capsule", "runway", "collection", "streetwear",
    "trend", "sneaker", "denim", "leather", "vintage", "archive", "silhouette",
    "fashion week", "показ", "коллекц", "стритвир", "мерч", "дроп", "тренд",
]


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch(url: str, timeout: int = 15) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.5",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def fetch_response(url: str, timeout: int = 15):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"})
    return urllib.request.urlopen(req, timeout=timeout)


def text(node: ET.Element | None, default: str = "") -> str:
    return clean(node.text if node is not None else default)


def first_image(item: ET.Element) -> str | None:
    for child in item.iter():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag in {"content", "thumbnail"}:
            url = child.attrib.get("url")
            if url and url.startswith("http"):
                return url
        if tag == "enclosure":
            url = child.attrib.get("url")
            kind = child.attrib.get("type", "")
            if url and (kind.startswith("image/") or re.search(r"\.(?:jpg|jpeg|png|webp|avif)(?:$|\?)", url, re.I)):
                return url
    return None


def og_image(url: str) -> str | None:
    """Read the public page head and extract its publisher-selected image."""
    try:
        raw = fetch(url, timeout=8).decode("utf-8", errors="ignore")[:350_000]
    except Exception:
        return None
    patterns = [
        r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::secure_url)?["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.I)
        if match:
            candidate = html.unescape(match.group(1).strip())
            if candidate.startswith("//"):
                candidate = "https:" + candidate
            if candidate.startswith("http"):
                return candidate
    return None


def editorial_brief(title: str, description: str, source: str, category: str) -> str:
    """Turn the public feed excerpt into a readable in-app editorial brief.

    This deliberately does not scrape or reproduce full articles. It keeps the
    user's reading experience inside ASStylist while leaving the source link
    available for the full original story.
    """
    desc = clean(description)
    desc = re.sub(r"\b(read more|continue reading|читать далее)\b.*$", "", desc, flags=re.I).strip(" .—–")
    desc = re.sub(r"^\s*(источник|source)\s*:\s*[^.]+[.]?\s*", "", desc, flags=re.I)
    if not desc:
        return f"{title}. Редакция ASStylist собрала главное из открытого материала {source.lower()} и оставила короткий контекст, чтобы понять, почему эта история сейчас важна для моды."

    sentences = re.split(r"(?<=[.!?])\s+", desc)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    base = " ".join(sentences[:4]).strip()
    if len(base) < 180 and len(sentences) > 4:
        base = " ".join(sentences[:6]).strip()
    if len(base) > 850:
        base = base[:850].rsplit(" ", 1)[0].rstrip(" ,;:—–") + "…"

    lead = {
        "world": "Что происходит: ",
        "russian-streetwear": "Что происходит на локальной сцене: ",
        "runway": "Что показали: ",
        "merch": "Что вышло: ",
        "social-trends": "Что залетает в соцсетях: ",
    }.get(category, "Что происходит: ")
    return lead + base


def cache_image(url: str | None, article_id: str) -> str | None:
    if not url:
        return None
    try:
        with fetch_response(url, timeout=12) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            data = response.read(3_500_000)
        if not data or len(data) < 5000:
            return None
        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        elif "avif" in content_type:
            ext = ".avif"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        else:
            path_ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
            if path_ext in {".jpg", ".jpeg", ".png", ".webp", ".avif"}:
                ext = ".jpg" if path_ext == ".jpeg" else path_ext
        target = IMAGE_DIR / f"{article_id}{ext}"
        target.write_bytes(data)
        return f"/journal-images/{target.name}"
    except Exception as exc:
        print(f"[journal] image cache failed: {url}: {exc}")
        return None


def parse_date(value: str) -> datetime:
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(value).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def google_news_url(query: str) -> str:
    encoded = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl=ru&gl=RU&ceid=RU:ru"


def score(article: dict) -> float:
    age_days = max(0.0, (datetime.now(timezone.utc) - parse_date(article["published_at"])).total_seconds() / 86400)
    freshness = max(0.0, 1.0 - age_days / 8.0)
    source = TRUST.get(article["source"], 0.65)
    words = (article["title"] + " " + article["summary"]).lower()
    relevance = min(1.0, sum(1 for key in KEYWORDS if key in words) / 4.0)
    return freshness * 0.55 + source * 0.25 + relevance * 0.20


def main() -> None:
    now = datetime.now(timezone.utc)
    week_end = now.date()
    week_start = week_end - timedelta(days=6)
    articles: list[dict] = []
    seen: set[str] = set()

    if IMAGE_DIR.exists():
        shutil.rmtree(IMAGE_DIR)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    for category, query, label in FEEDS:
        try:
            root = ET.fromstring(fetch(google_news_url(query)))
        except Exception as exc:
            print(f"[journal] feed failed: {label}: {exc}")
            continue
        for item in root.findall(".//item"):
            title = text(item.find("title"))
            url = text(item.find("link"))
            if not title or not url:
                continue
            published = parse_date(text(item.find("pubDate")))
            if published.date() < week_start:
                continue
            source = text(item.find("source")) or "Открытый источник"
            summary = text(item.find("description"))
            key = re.sub(r"[^a-zа-я0-9]", "", title.lower())[:160]
            if key in seen:
                continue
            seen.add(key)
            image = first_image(item) or og_image(url)
            articles.append({
                "id": key or str(len(articles)),
                "title": title,
                "summary": summary[:360],
                "editorial": editorial_brief(title, summary, source, category),
                "url": url,
                "source": source,
                "published_at": published.isoformat(),
                "category": category,
                "image_url": image,
                "tags": [label],
            })

    articles.sort(key=score, reverse=True)
    selected: list[dict] = []
    counts: Counter[str] = Counter()
    for article in articles:
        category = article["category"]
        if counts[category] >= 6:
            continue
        selected.append(article)
        counts[category] += 1
        if len(selected) >= 30:
            break

    cached = 0
    for article in selected:
        cached_url = cache_image(article.get("image_url"), article["id"])
        if cached_url:
            article["image_url"] = cached_url
            cached += 1
        else:
            article["image_url"] = None

    corpus = " ".join(a["title"] + " " + a["summary"] for a in selected).lower()
    trend_terms = ["oversized", "baggy", "red", "brown", "denim", "vintage", "archive", "sneaker", "leather", "layering"]
    trend_counts = Counter(term for term in trend_terms if term in corpus)
    trend = trend_counts.most_common(1)[0][0] if trend_counts else "смешение архивных и новых силуэтов"
    trend_note = f"Главный сигнал недели: {trend}. Это частота упоминаний в открытых источниках, а не прогноз."

    lead = selected[0]["title"] if selected else "Новый выпуск уже собирается."
    iso_week = now.isocalendar().week
    year = now.isocalendar().year
    payload = {
        "issue": int(f"{year % 100:02d}{iso_week:02d}"),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "generated_at": now.isoformat(),
        "lead": lead,
        "trend_note": trend_note,
        "articles": selected,
        "source_count": len(FEEDS),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[journal] wrote {len(selected)} articles ({cached} cached images) -> {OUT}")


if __name__ == "__main__":
    main()
