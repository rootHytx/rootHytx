#!/usr/bin/env python3
"""
Update README.md with:
  1. Most active repos (from GitHub API)
  2. Typing SVG animation (from quotes.txt)
"""

import os
import re
import requests
from datetime import datetime, timezone
from urllib.parse import quote

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]
README_PATH = "README.md"
QUOTES_PATH = "quotes.txt"

REPOS_START = "<!-- MOST_ACTIVE_REPOS_START -->"
REPOS_END = "<!-- MOST_ACTIVE_REPOS_END -->"
SVG_START = "<!-- TYPING_SVG_START -->"
SVG_END = "<!-- TYPING_SVG_END -->"


# ── repos ──────────────────────────────────────────────────────

def fetch_repos(username: str, token: str) -> list[dict]:
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed&direction=desc&type=owner"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    repos = resp.json()
    return [r for r in repos if r["name"] != username and not r["fork"]]


def build_table(repos: list[dict], count: int = 6) -> str:
    lines = ["| # | Repository | ⭐ | Activity |", "|---|-----------|------|----------|"]
    for i, repo in enumerate(repos[:count], start=1):
        name = repo["name"]
        url = repo["html_url"]
        stars = repo["stargazers_count"]
        pushed = repo["pushed_at"]
        dt = datetime.strptime(pushed, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        if delta.days == 0:
            ago = "today"
        elif delta.days == 1:
            ago = "yesterday"
        elif delta.days < 30:
            ago = f"{delta.days} days ago"
        elif delta.days < 365:
            ago = f"{delta.days // 30} months ago"
        else:
            ago = f"{delta.days // 365} years ago"
        lines.append(f"| {i} | [{name}]({url}) | ★ {stars} | {ago} |")
    return "\n".join(lines)


# ── quotes / typing SVG ────────────────────────────────────────

def read_quotes(path: str) -> list[str]:
    """Read quotes.txt — one phrase per line, blanks and comments skipped."""
    with open(path, "r") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def build_typing_svg(quotes: list[str]) -> str:
    """Build the readme-typing-svg img tag from a list of plain-text quotes."""
    encoded = ";".join(quote(q) for q in quotes)
    url = (
        "https://readme-typing-svg.demolab.com"
        "?font=Fira+Code"
        "&size=14"
        "&duration=3000"
        "&pause=1500"
        "&color=e79cfe"
        "&center=true"
        "&vCenter=true"
        "&width=800"
        f"&lines={encoded}"
    )
    return (
        '<p align="center">\n'
        f'  <img src="{url}" alt="Terminal Typing" />\n'
        '</p>'
    )


# ── readme patching ────────────────────────────────────────────

def replace_between(content: str, start_marker: str, end_marker: str, replacement: str) -> str:
    pattern = re.compile(
        f"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
        re.DOTALL,
    )
    if not pattern.search(content):
        print(f"⚠ Skipping repo table — markers not found in {README_PATH}")
        return content
    return pattern.sub(f"{start_marker}\n{replacement}\n{end_marker}", content)


def update_readme(repos_table: str, typing_svg: str) -> None:
    with open(README_PATH, "r") as f:
        content = f.read()

    content = replace_between(content, REPOS_START, REPOS_END, repos_table)
    content = replace_between(content, SVG_START, SVG_END, typing_svg)

    with open(README_PATH, "w") as f:
        f.write(content)

    print(f"✅ Updated {README_PATH}")


# ── main ───────────────────────────────────────────────────────

if __name__ == "__main__":
    repos = fetch_repos(USERNAME, TOKEN)
    table = build_table(repos) if repos else ""

    quotes = read_quotes(QUOTES_PATH)
    if not quotes:
        raise SystemExit(f"No quotes found in {QUOTES_PATH}")
    svg = build_typing_svg(quotes)

    update_readme(table, svg)
