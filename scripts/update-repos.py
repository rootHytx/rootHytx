#!/usr/bin/env python3
"""
Fetch most active repos and update README.md's dynamic block.
Sorted by most recently pushed.
"""

import os
import re
import requests
from datetime import datetime, timezone

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]
README_PATH = "README.md"

START_MARKER = "<!-- MOST_ACTIVE_REPOS_START -->"
END_MARKER = "<!-- MOST_ACTIVE_REPOS_END -->"


def fetch_repos(username: str, token: str) -> list[dict]:
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed&direction=desc&type=owner"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    repos = resp.json()

    # Exclude the profile README repo itself
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


def update_readme(new_table: str) -> None:
    with open(README_PATH, "r") as f:
        content = f.read()

    pattern = re.compile(
        f"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL,
    )
    replacement = f"{START_MARKER}\n{new_table}\n{END_MARKER}"

    if not pattern.search(content):
        raise SystemExit(f"Markers not found in {README_PATH}")

    new_content = pattern.sub(replacement, content)

    with open(README_PATH, "w") as f:
        f.write(new_content)

    print(f"Updated {README_PATH} with top {new_table.count(chr(10)) - 2} repos.")


if __name__ == "__main__":
    repos = fetch_repos(USERNAME, TOKEN)
    if not repos:
        raise SystemExit("No repos found — check your token permissions.")
    table = build_table(repos)
    update_readme(table)
