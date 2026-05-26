#!/usr/bin/env python3
"""
fetch-reddit-posts.py — Fetch recent posts from a university's subreddit.

Usage:
    python scripts/fetch-reddit-posts.py <subreddit> [query] [limit] [output_file]

Arguments:
    subreddit       Required. The subreddit name (e.g., UWMadison, gatech, UIUC)
    query           Optional. Search query (default: "computer science program")
    limit           Optional. Max posts to fetch (default: 25, max: 100)
    output_file     Optional. Path to write JSON output (default: print to stdout)

Output:
    JSON with post titles, scores, comment counts, URLs, selftext,
    and top comments (score > 1, up to 8 per post).

Examples:
    python scripts/fetch-reddit-posts.py UWMadison
    python scripts/fetch-reddit-posts.py UWMadison "AI machine learning" 15
    python scripts/fetch-reddit-posts.py UWMadison "computer science" 25 output.json

Notes:
    - Uses old.reddit.com JSON API (no auth required).
    - Filters to posts within the past year (t=year).
    - Reddit data is anecdotal — always mark as "student perspective" in reports.
    - On Windows, use output_file to avoid stdout encoding issues.
"""

import urllib.request
import urllib.parse
import json
import sys


def main():
    # ── Parse arguments ─────────────────────────────────────────────
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    subreddit = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else "computer science program"
    limit = min(int(sys.argv[3]) if len(sys.argv) > 3 else 25, 100)
    output_file = sys.argv[4] if len(sys.argv) > 4 else None

    # ── Fetch search results ────────────────────────────────────────
    search_url = (
        f"https://old.reddit.com/r/{subreddit}/search.json"
        f"?q={urllib.parse.quote(query)}&sort=new&t=year&restrict_sr=on&limit={limit}"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    req = urllib.request.Request(search_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8").replace("\xa0", " ")
            search_data = json.loads(raw)
    except Exception as e:
        error_msg = json.dumps({"error": f"Search failed: {e}"}, ensure_ascii=False)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(error_msg)
        else:
            print(error_msg)
        sys.exit(1)

    posts = search_data.get("data", {}).get("children", [])
    results = []

    for post in posts[:limit]:
        d = post["data"]
        entry = {
            "title": d.get("title", "")[:200],
            "score": d.get("score", 0),
            "num_comments": d.get("num_comments", 0),
            "url": d.get("url", ""),
            "created_utc": d.get("created_utc", 0),
            "selftext": d.get("selftext", "")[:1000].replace("\xa0", " "),
            "top_comments": [],
        }

        # ── Fetch comments for this post ────────────────────────────
        permalink = d.get("permalink", "")
        if permalink:
            comments_url = f"https://old.reddit.com{permalink}.json"
            try:
                c_req = urllib.request.Request(comments_url, headers=headers)
                with urllib.request.urlopen(c_req, timeout=10) as c_resp:
                    c_raw = c_resp.read().decode("utf-8").replace("\xa0", " ")
                    c_data = json.loads(c_raw)
            except Exception:
                c_data = None

            if c_data and len(c_data) > 1:
                comments = c_data[1].get("data", {}).get("children", [])
                count = 0
                for c in comments:
                    if c["kind"] == "t1":
                        body = c["data"].get("body", "")[:500].replace("\xa0", " ")
                        score = c["data"].get("score", 0)
                        if score > 1 and body.strip():
                            entry["top_comments"].append({
                                "score": score,
                                "body": body,
                            })
                            count += 1
                            if count >= 8:
                                break

        results.append(entry)

    # ── Output ──────────────────────────────────────────────────────
    output = json.dumps(results, ensure_ascii=False, indent=2)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
            f.write("\n")
        print(f"Wrote {len(results)} posts to {output_file}", file=sys.stderr)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(output)


if __name__ == "__main__":
    main()
