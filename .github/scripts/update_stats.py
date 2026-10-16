#!/usr/bin/env python3
"""Refresh the numbers in README.md between <!-- stat:KEY --> and <!-- /stat --> markers.

Usage: python3 .github/scripts/update_stats.py README.md

Only keys that have a marker in the README are fetched. A failed or odd fetch
keeps the number already in the README, and the script still exits 0.
GitHub stars are shown as is; Docker Hub pulls are rounded down to the
nearest 100, matching the "about 29,700" style of the README.
"""
import json
import os
import re
import sys
import urllib.request

MARKER = re.compile(r"(<!-- stat:([a-z0-9-]+) -->)(.*?)(<!-- /stat -->)")

# key: (source, name, round down to)
STATS = {
    "deleterr-stars": ("github-stars", "rfsbraz/deleterr", 1),
    "deleterr-pulls": ("docker-pulls", "rfsbraz/deleterr", 100),
    "telegram-downloader-pulls": ("docker-pulls", "rfsbraz/telegram-downloader", 100),
}


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "rfsbraz-readme-stats", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def fetch(key):
    source, name, _ = STATS[key]
    if source == "github-stars":
        headers = {"Accept": "application/vnd.github+json"}
        if os.environ.get("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
        return get_json(f"https://api.github.com/repos/{name}", headers)["stargazers_count"]
    return get_json(f"https://hub.docker.com/v2/repositories/{name}/")["pull_count"]


def format_value(key, value):
    step = STATS[key][2]
    return f"{value // step * step:,}"


def update(text, fetcher):
    """Return the new text and rows of (key, old, fetched, new)."""
    rows = []
    cache = {}

    def replace(m):
        key, old = m.group(2), m.group(3)
        if key not in STATS:
            return m.group(0)
        if key not in cache:
            try:
                value = fetcher(key)
                if type(value) is not int or value <= 0:
                    raise ValueError(f"unexpected value {value!r}")
                cache[key] = value
            except Exception as e:  # keep the README value on any failure
                print(f"::warning::{key}: fetch failed ({e}), keeping {old}")
                cache[key] = None
        value = cache[key]
        new = old if value is None else format_value(key, value)
        rows.append((key, old, value, new))
        return m.group(1) + new + m.group(4)

    return MARKER.sub(replace, text), rows


def main(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new, rows = update(text, fetch)
    for key, old, value, out in rows:
        print(f"{key}: README {old}, fetched {value if value is not None else 'failed'}, writes {out}")
    if new != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "README.md")
