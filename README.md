# The Fragrance Gazette — automated pipeline

Rebuilds `docs/index.html` on a schedule, from real RSS feeds plus a
hand-maintained file for the things no feed can give you. Free to run
on GitHub's own infrastructure.

## What's actually automated, and what isn't

| Section              | Source                          | Updates how           |
|-----------------------|----------------------------------|------------------------|
| This Week / This Month | Live RSS (`fetch_and_build.py`) | Automatically, daily   |
| Archive by month       | Same feeds, accumulated         | Automatically, daily   |
| Buzz ranking            | `data/manual.json`              | You edit it by hand    |
| Pop-ups                 | `data/manual.json`              | You edit it by hand    |
| Exhibitions / Innovation / Trends | `data/manual.json`   | You edit it by hand    |

The bottom three rows are not a gap I forgot — they need paid social
listening (buzz), a human watching Instagram (pop-ups), or move too
slowly for daily automation to matter (exhibitions, innovation, trends).
Automating them would mean either paying for a listening tool or faking
data. Neither is on offer here.

## One-time setup (about 15 minutes)

1. **Create a free GitHub account** if your team doesn't have one, and
   a new **public** repository — name it whatever you like.
   (GitHub Pages' free tier only serves public repos. The content here
   is all public trade-press information, so that's a non-issue —
   but if you'd rather keep it private, that needs GitHub Enterprise
   or a different host such as Cloudflare Pages with access control.)

2. **Upload this whole folder** to that repo — via the GitHub web
   uploader, or `git push` if someone on your team is comfortable with
   git.

3. **Turn on GitHub Pages**: repo Settings → Pages → Source: "Deploy
   from a branch" → Branch: `main`, folder: `/docs` → Save.
   GitHub will give you a URL like
   `https://yourusername.github.io/your-repo-name/` — that's the link
   for the whole team.

4. **Run it once by hand** to populate the page immediately, instead
   of waiting for the schedule: repo → Actions tab → "Update Fragrance
   Gazette" → Run workflow. Check the log — if it says
   `0 feed items this run`, the feed URL needs checking (see below).

5. After that, it runs itself daily at 06:00 UTC (edit the `cron` line
   in `.github/workflows/update.yml` to change the time — cron syntax,
   UTC only).

## Adding more feeds

`FEEDS` near the top of `fetch_and_build.py` is the only place sources
are configured. Before adding one:

- Open the candidate URL directly in a browser. A real feed shows raw
  XML starting with `<?xml ...><rss ...>`. A normal webpage is not a
  feed, even if the site clearly has one somewhere.
- Common patterns to try: `example.com/feed/` (WordPress sites),
  `example.com/rss.xml`, `example.com/feed.xml`. There's no universal
  rule — you have to check per site.
- A broken feed URL doesn't crash the build; it logs a warning and the
  run continues with whatever else worked. Check the Actions log after
  adding one.

I confirmed `nstperfume.com/feed/` (Now Smell This) is correct, from
their own migration notice. I could not verify Fragrantica's,
Premium Beauty News's, or Nez's exact feed paths — they're commented
out in the script rather than guessed at.

**Nez specifically**: the content lives at `mag.bynez.com`, not
`bynez.com` (that's their corporate homepage, no articles). It's
WordPress, so `mag.bynez.com/feed/` is the best-guess default —
try that first, and `mag.bynez.com/en/feed/` if it 404s, since their
multilingual plugin sometimes moves the feed under the language
prefix and sometimes doesn't. Open whichever one in a browser; if you
see raw XML, uncomment that line in `fetch_and_build.py`, commit, and
it's live on the next run.

## Editing the manual sections

Open `data/manual.json`. It's one field, `static_sections`, holding
HTML as a string — that's what lands between "This Month" and the
Archive on the page. Edit it directly (mind the escaped quotes), commit,
and the next scheduled run will pick it up. It is never touched by the
script itself.

## If something breaks

- **Page stops updating**: check the Actions tab for a red X. Most
  likely cause is a feed URL that stopped resolving — sites do retire
  RSS feeds without warning.
- **Archive looks wrong or duplicated**: `data/archive.json` is the
  source of truth; you can hand-edit it same as the manual file.
- **Nothing in "This Week"**: normal if it's genuinely been a quiet
  week for whatever's in `FEEDS` — the page says so rather than showing
  nothing.
