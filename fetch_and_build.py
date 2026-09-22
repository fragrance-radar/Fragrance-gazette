#!/usr/bin/env python3
"""
Fragrance Gazette — automated builder.

Pulls RSS feeds, buckets items into "this week" (7d) and "this month" (30d)
using each item's REAL published date (not a hardcoded string — this is
what makes the date on the page actually move), merges new items into a
persistent month-by-month archive, drops in the hand-maintained sections
(buzz ranking, pop-ups, exhibitions, innovation, trends), and writes
docs/index.html for GitHub Pages to serve.

Run locally:  pip install -r requirements.txt && python fetch_and_build.py
Run in CI:    see .github/workflows/update.yml — this is what makes it
              run without you typing anything, on the schedule you set.
"""
import json, datetime, html, re
from pathlib import Path

try:
    import feedparser
except ImportError:
    raise SystemExit("Missing dependency. Run: pip install -r requirements.txt")

ROOT = Path(__file__).parent
ARCHIVE_PATH = ROOT / "data" / "archive.json"
MANUAL_PATH = ROOT / "data" / "manual.json"
TEMPLATE_PATH = ROOT / "template.html"
OUT_PATH = ROOT / "docs" / "index.html"

# --- Feeds -------------------------------------------------------------
# Only add a feed once you've confirmed the URL actually resolves and
# returns RSS/Atom XML — a wrong URL is silently skipped (see fetch_all),
# so a typo here just means fewer items, not a crash. Test a candidate
# feed by opening it in a browser: valid RSS shows raw XML, not a webpage.
FEEDS = [
    {"url": "https://nstperfume.com/feed/", "name": "Now Smell This"},
    # Candidates worth checking yourself (unverified as of this build —
    # confirm before uncommenting, see README "Adding more feeds"):
    # {"url": "https://mag.bynez.com/feed/", "name": "Nez"},          # try this one first
    # {"url": "https://mag.bynez.com/en/feed/", "name": "Nez (EN)"},  # try this if the above 404s
    # {"url": "https://www.fragrantica.com/rss/news.xml", "name": "Fragrantica"},
    # {"url": "https://www.premiumbeautynews.com/xml/syndication.rss", "name": "Premium Beauty News"},
    # {"url": "https://www.perfumerflavorist.com/rss/", "name": "Perfumer & Flavorist"},
]

def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def strip_tags(text):
    return re.sub(r"<[^<]+?>", "", text or "").strip()

def fetch_all():
    items = []
    for feed in FEEDS:
        try:
            parsed = feedparser.parse(feed["url"])
            if not parsed.entries:
                print(f"[warn] {feed['name']}: 0 entries returned — check the feed URL")
                continue
            for e in parsed.entries[:30]:
                pub = e.get("published_parsed") or e.get("updated_parsed")
                dt = datetime.datetime(*pub[:6]) if pub else datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                items.append({
                    "title": html.unescape(e.get("title", "Untitled")),
                    "link": e.get("link", "#"),
                    "summary": html.unescape(strip_tags(e.get("summary", "")))[:220],
                    "source": feed["name"],
                    "date": dt.strftime("%Y-%m-%d"),
                })
        except Exception as ex:
            print(f"[warn] {feed['name']} failed: {ex}")
    return items

def bucket(items, days):
    cutoff = (datetime.datetime.now(datetime.timezone.utc)
              - datetime.timedelta(days=days)).replace(tzinfo=None)
    return [i for i in items if datetime.datetime.strptime(i["date"], "%Y-%m-%d") >= cutoff]

def render_items(items, empty_msg):
    if not items:
        return f'<p class="warn">{empty_msg}</p>'
    out = []
    for i in items:
        out.append(
            f'<div class="item"><div class="meta sans">{i["date"]} · {i["source"]}</div>'
            f'<h3>{i["title"]}</h3><p>{i["summary"]} <a href="{i["link"]}">Source</a></p></div>'
        )
    return "\n".join(out)

def merge_archive(archive, items):
    seen = {i["link"] for month_items in archive.values() for i in month_items}
    for i in items:
        month = datetime.datetime.strptime(i["date"], "%Y-%m-%d").strftime("%B")
        if i["link"] not in seen:
            archive.setdefault(month, []).append(i)
            seen.add(i["link"])
    return archive

def render_archive(archive):
    order = ["January","February","March","April","May","June","July",
             "August","September","October","November","December"]
    out = []
    for m in order:
        if archive.get(m):
            out.append(f"<h4>{m}</h4><ul>")
            for i in archive[m]:
                out.append(
                    f'<li><b>{i["title"]}</b> '
                    f'<span class="src">— {i["source"]}, <a href="{i["link"]}">source</a></span></li>'
                )
            out.append("</ul>")
    return "\n".join(out) if out else "<p>Archive is empty.</p>"

def main():
    archive = load_json(ARCHIVE_PATH, {})
    manual = load_json(MANUAL_PATH, {"static_sections": "<p>No manual sections set — see data/manual.json.</p>"})

    items = fetch_all()
    archive = merge_archive(archive, items)
    save_json(ARCHIVE_PATH, archive)

    today = datetime.date.today().strftime("%d %B %Y")
    tmpl = TEMPLATE_PATH.read_text(encoding="utf-8")
    out = (tmpl
        .replace("{{DATE}}", today)
        .replace("{{WEEK_ITEMS}}", render_items(bucket(items, 7),
            "No feed items landed this week. Either a quiet week, or a feed needs checking."))
        .replace("{{MONTH_ITEMS}}", render_items(bucket(items, 30),
            "No feed items landed this month. Check FEEDS in fetch_and_build.py."))
        .replace("{{STATIC}}", manual.get("static_sections", ""))
        .replace("{{ARCHIVE}}", render_archive(archive)))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(out, encoding="utf-8")
    total_archived = sum(len(v) for v in archive.values())
    print(f"Wrote {OUT_PATH} — {len(items)} feed items this run, {total_archived} total in archive.")

if __name__ == "__main__":
    main()
