"""
fetch_news.py — Fetches RSS feeds and generates news.json for mechanistlab.com
Run manually or via GitHub Actions (daily).
Produces up to 20 articles per source (60 total max), sorted by date.
"""
import feedparser
import json
import re
from datetime import datetime

FEEDS = [
    {
        'url': 'https://spacenews.com/feed/',
        'source': 'SpaceNews',
        'category': 'aerospace',
        'color': '#1a6da8',
        'keywords': None
    },
    {
        'url': 'https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml',
        'source': 'Defense News',
        'category': 'defense',
        'color': '#8b1a1a',
        'keywords': [
            'technology', 'system', 'aircraft', 'satellite', 'drone', 'UAV',
            'missile', 'sensor', 'radar', 'propulsion', 'material', 'structure',
            'hypersonic', 'research', 'program', 'development', 'test', 'space',
            'cyber', 'weapon', 'Pentagon', 'contract', 'budget', 'engine', 'armor'
        ]
    },
    {
        'url': 'https://www.sciencedaily.com/rss/matter_energy/engineering.xml',
        'source': 'ScienceDaily',
        'category': 'engineering',
        'color': '#2a9d8f',
        'keywords': None
    }
]


def strip_html(text):
    return re.sub(r'<[^>]+>', '', text or '').strip()


def parse_date(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6]).isoformat() + 'Z'
        except Exception:
            pass
    return ''


PER_SOURCE_CAP = 20

items = []
for cfg in FEEDS:
    try:
        feed = feedparser.parse(cfg['url'])
        source_items = []
        for entry in feed.entries[:50]:  # fetch more, then cap after filtering
            title = strip_html(entry.get('title', ''))
            link = entry.get('link', '')
            pub_date = parse_date(entry)
            desc = strip_html(entry.get('summary', entry.get('description', '')))
            snippet = (desc[:200] + '...') if len(desc) > 200 else desc

            if cfg['keywords']:
                haystack = (title + ' ' + desc).lower()
                if not any(kw.lower() in haystack for kw in cfg['keywords']):
                    continue
            if not title or len(title) < 10:
                continue

            source_items.append({
                'title': title,
                'link': link,
                'pubDate': pub_date,
                'snippet': snippet,
                'source': cfg['source'],
                'category': cfg['category'],
                'color': cfg['color']
            })

        # Sort by date and cap at PER_SOURCE_CAP
        source_items.sort(key=lambda x: x['pubDate'], reverse=True)
        source_items = source_items[:PER_SOURCE_CAP]
        items.extend(source_items)
        print(f"{cfg['source']}: {len(source_items)} items")
    except Exception as e:
        print(f"ERROR {cfg['source']}: {e}")

# Merge and sort all sources by date
items.sort(key=lambda x: x['pubDate'], reverse=True)

# Deduplicate by title prefix
seen = set()
deduped = []
for item in items:
    key = item['title'].lower()[:60]
    if key not in seen:
        seen.add(key)
        deduped.append(item)

output = {
    'updated': datetime.utcnow().isoformat() + 'Z',
    'count': len(deduped),
    'items': deduped
}

with open('news.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nDone: {len(deduped)} unique items saved to news.json")
