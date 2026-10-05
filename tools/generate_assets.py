#!/usr/bin/env python3
"""Generate self-hosted profile assets for github.com/ahmad2422.

Produces:
  assets/stats.svg        - stats card (repos / followers / stars / contributions + top languages)
  assets/icons/*.svg      - brand icon tiles matching the skillicons.dev look

Runs with only the standard library. Set GITHUB_TOKEN to enrich the card with
contribution counts from the GraphQL API (the Action provides it automatically).
"""
import datetime
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

USER = "ahmad2422"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
UA = {"User-Agent": "ahmad2422-profile-assets", "Accept": "application/vnd.github+json"}

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
ICONS = OUT / "icons"

LANG_COLORS = {
    "TypeScript": "#3178C6", "JavaScript": "#F7DF1E", "HTML": "#E34F26", "CSS": "#1572B6",
    "PHP": "#777BB4", "C": "#A8B9CC", "C++": "#00599C", "Rust": "#DEA584", "Astro": "#FF5D01",
    "Python": "#3572A5", "Shell": "#89E051", "Vue": "#41B883", "Go": "#00ADD8",
    "Java": "#B07219", "SCSS": "#C6538C", "MDX": "#FCB32C",
}
FALLBACK_COLORS = ["#22d3ee", "#818cf8", "#e879f9", "#f472b6", "#34d399", "#fbbf24"]

# slug on simple-icons, output filename, label, tile colour, glyph colour
ICON_SPECS = [
    ("framer", "framer", "Framer Motion", "0055FF", "#ffffff"),
    ("greensock", "gsap", "GSAP", "88CE02", "#0b1120"),
    ("githubactions", "ghactions", "GitHub Actions", "2088FF", "#ffffff"),
    ("openai", "openai", "OpenAI", "412991", "#ffffff"),
    ("claude", "claude", "Claude", "D97757", "#ffffff"),
    ("modelcontextprotocol", "mcp", "MCP", "111827", "#ffffff"),
    ("ollama", "ollama", "Ollama", "111827", "#ffffff"),
]


def fetch_json(url):
    req = urllib.request.Request(url, headers=UA)
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def graphql(query):
    if not TOKEN:
        return None
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={**UA, "Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except Exception as exc:  # noqa: BLE001 - the card still renders without this
        print("  graphql unavailable:", exc)
        return None


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_stats_svg(stats, langs):
    """stats: list of (label, value). langs: list of (name, pct, colour)."""
    tiles = []
    x, w, gap, y, h = 40, 265, 20, 50, 100
    for i, (label, value) in enumerate(stats):
        tx = x + i * (w + gap)
        tiles.append(
            f'<rect x="{tx}" y="{y}" width="{w}" height="{h}" rx="16" fill="#0d1526" stroke="#1e293b" stroke-width="1.5"/>'
            f'<text x="{tx + w // 2}" y="{y + 58}" text-anchor="middle" font-family="\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif" '
            f'font-size="40" font-weight="700" fill="url(#accent)">{esc(value)}</text>'
            f'<text x="{tx + w // 2}" y="{y + 84}" text-anchor="middle" font-family="\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif" '
            f'font-size="15" fill="#94a3b8" letter-spacing="1.2">{esc(label)}</text>'
        )

    bar_x, bar_y, bar_w, bar_h = 40, 208, 1120, 16
    segs, legend = [], []
    cursor = bar_x
    for i, (name, pct, colour) in enumerate(langs):
        width = bar_w * pct / 100.0
        segs.append(f'<rect x="{cursor:.1f}" y="{bar_y}" width="{width:.1f}" height="{bar_h}" fill="{colour}"/>')
        lx = bar_x + i * (bar_w / max(len(langs), 1))
        legend.append(
            f'<circle cx="{lx + 6:.1f}" cy="253" r="5" fill="{colour}"/>'
            f'<text x="{lx + 18:.1f}" y="258" font-family="\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif" '
            f'font-size="14" fill="#c9d1d9">{esc(name)} <tspan fill="#7d8ea8">{pct:.0f}%</tspan></text>'
        )
        cursor += width

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 300" width="1200" height="300" role="img" aria-label="GitHub statistics for {USER}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#05070f"/><stop offset="50%" stop-color="#121c42"/><stop offset="100%" stop-color="#03202c"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#22d3ee"><animate attributeName="stop-color" values="#22d3ee;#818cf8;#e879f9;#22d3ee" dur="10s" repeatCount="indefinite"/></stop>
      <stop offset="100%" stop-color="#e879f9"><animate attributeName="stop-color" values="#e879f9;#22d3ee;#818cf8;#e879f9" dur="10s" repeatCount="indefinite"/></stop>
    </linearGradient>
    <filter id="soft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="50"/></filter>
    <clipPath id="barc"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="8"/></clipPath>
  </defs>
  <rect width="1200" height="300" fill="url(#bg)"/>
  <circle cx="140" cy="70" r="130" fill="#4338ca" opacity="0.5" filter="url(#soft)">
    <animate attributeName="cx" values="140;340;140" dur="16s" repeatCount="indefinite"/>
  </circle>
  <circle cx="1060" cy="240" r="140" fill="#0891b2" opacity="0.45" filter="url(#soft)">
    <animate attributeName="cx" values="1060;820;1060" dur="19s" repeatCount="indefinite"/>
  </circle>
  {''.join(tiles)}
  <text x="{bar_x}" y="196" font-family="'Segoe UI',Roboto,Helvetica,Arial,sans-serif" font-size="15" fill="#94a3b8" letter-spacing="1.5">TOP LANGUAGES ACROSS REPOSITORIES</text>
  <g clip-path="url(#barc)">{''.join(segs)}</g>
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="8" fill="none" stroke="#1e293b" stroke-width="1.5"/>
  {''.join(legend)}
  <text x="1160" y="288" text-anchor="end" font-family="'Segoe UI',Roboto,Helvetica,Arial,sans-serif" font-size="12" fill="#475569">updated {stamp}</text>
</svg>
'''


def build_icon_tiles():
    made = []
    for slug, fname, label, colour, glyph in ICON_SPECS:
        try:
            raw = fetch_text(f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg")
        except Exception as exc:  # noqa: BLE001
            print(f"  skip {slug}: {exc}")
            continue
        match = re.search(r'd="([^"]+)"', raw)
        if not match:
            print(f"  skip {slug}: no path data")
            continue
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48" '
            f'role="img" aria-label="{label}"><rect width="48" height="48" rx="10" fill="#{colour}"/>'
            f'<g transform="translate(10.2,10.2) scale(1.15)"><path fill="{glyph}" d="{match.group(1)}"/></g></svg>'
        )
        (ICONS / f"{fname}.svg").write_text(svg, encoding="utf-8")
        made.append(fname)
    return made


def main():
    ICONS.mkdir(parents=True, exist_ok=True)

    user = fetch_json(f"https://api.github.com/users/{USER}")
    repos = fetch_json(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    own = [r for r in repos if not r.get("fork")]

    stars = sum(r.get("stargazers_count", 0) for r in own)
    counts = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1

    total = sum(counts.values()) or 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
    langs = []
    for i, (name, count) in enumerate(ranked):
        colour = LANG_COLORS.get(name, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        langs.append((name, count * 100.0 / total, colour))

    contributions = None
    data = graphql('{ user(login: "%s") { contributionsCollection { contributionCalendar { totalContributions } } } }' % USER)
    if data and data.get("data", {}).get("user"):
        contributions = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    if contributions is not None:
        stat_pairs = [("Public repos", user["public_repos"]), ("Followers", user["followers"]),
                      ("Stars earned", stars), ("Contributions 1y", contributions)]
    else:
        stat_pairs = [("Public repos", user["public_repos"]), ("Followers", user["followers"]),
                      ("Stars earned", stars), ("Following", user["following"])]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stats.svg").write_text(build_stats_svg(stat_pairs, langs), encoding="utf-8")
    print("  stats.svg:", stat_pairs, "|", [l[0] for l in langs])

    made = build_icon_tiles()
    print("  icons:", ", ".join(made) if made else "none")


if __name__ == "__main__":
    main()
