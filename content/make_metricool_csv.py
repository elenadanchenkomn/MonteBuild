"""Build a Metricool bulk-import CSV from content/posts.json.

Usage: python3 content/make_metricool_csv.py [YYYY-MM-DD-from] [YYYY-MM-DD-to]
Writes content/metricool/<from>_<to>.csv. Images are served from the public
`content` branch via raw.githubusercontent.com. Each post becomes two rows:
Instagram (with hashtags) and Facebook (without).
"""
import csv, json, pathlib, sys

REPO_RAW = "https://raw.githubusercontent.com/elenadanchenkomn/montebuild/content/content"
ROOT = pathlib.Path(__file__).resolve().parent

HEADERS = (
    ["Text", "Date", "Time", "Draft", "Facebook", "Twitter/X", "LinkedIn", "GBP",
     "Instagram", "Pinterest", "TikTok", "YouTube", "Threads", "Bluesky"]
    + [f"Picture Url {i}" for i in range(1, 11)]
    + [f"Alt text picture {i}" for i in range(1, 11)]
    + ["Document title", "Shortener", "Video Thumbnail Url", "Video Cover Frame",
       "Twitter/X Can reply", "Twitter/X Type", "Twitter/X Poll Duration minutes"]
    + [f"Twitter/X Poll Option {i}" for i in range(1, 5)]
    + ["Pinterest Board", "Pinterest Pin Title", "Pinterest Pin Link", "Pinterest Pin New Format",
       "Instagram Post Type", "Instagram Show Reel On Feed",
       "YouTube Video Title", "YouTube Video Type", "YouTube Video Privacy", "YouTube video for kids",
       "YouTube Video Category", "YouTube Video Tags", "YouTube Playlist", "YouTube Notify Subscribers",
       "GBP Post Type", "Facebook Post Type", "Facebook Title", "First Comment Text",
       "TikTok Title", "TikTok disable comments", "TikTok disable duet", "TikTok disable stitch",
       "TikTok Post Privacy (personal accounts only)", "TikTok Branded Content (personal accounts only)",
       "TikTok Your Brand (personal accounts only)", "TikTok Auto Add Music (personal accounts only)",
       "TikTok Photo Cover Index", "TikTok musicId", "TikTok music title", "TikTok music author",
       "TikTok music previewUrl", "TikTok music thumbnailUrl", "TikTok music soundVolume",
       "TikTok music originalVolume", "TikTok music startMillis", "TikTok music endMillis",
       "LinkedIn Type", "LinkedIn Poll Question"]
    + [f"LinkedIn Poll Option {i}" for i in range(1, 5)]
    + ["LinkedIn Poll Duration", "LinkedIn Show link preview", "LinkedIn Images as Carousel",
       "Threads Reply Control", "Threads Is Spoiler", "Threads Post Type", "Brand name (Optional)"]
)
NETWORKS = ["Facebook", "Twitter/X", "LinkedIn", "GBP", "Instagram", "Pinterest",
            "TikTok", "YouTube", "Threads", "Bluesky"]


def row(post, network):
    r = {h: "" for h in HEADERS}
    text = post["text"]
    if network == "Instagram" and post.get("hashtags"):
        text = f"{text}\n\n{post['hashtags']}"
    r.update({"Text": text, "Date": post["date"], "Time": post["time"], "Draft": "FALSE"})
    for n in NETWORKS:
        r[n] = "TRUE" if n == network else "FALSE"
    for i in range(1, post["slides"] + 1):
        r[f"Picture Url {i}"] = f"{REPO_RAW}/{post['folder']}/slide{i}.jpg"
        r[f"Alt text picture {i}"] = post.get("alt", "")
    if network == "Instagram":
        r["Instagram Post Type"] = "POST"
    else:
        r["Facebook Post Type"] = "POST"
    return r


def main():
    posts = json.loads((ROOT / "posts.json").read_text(encoding="utf-8"))
    lo = sys.argv[1] if len(sys.argv) > 1 else min(p["date"] for p in posts)
    hi = sys.argv[2] if len(sys.argv) > 2 else max(p["date"] for p in posts)
    sel = [p for p in posts if lo <= p["date"] <= hi]
    out = ROOT / "metricool" / f"{lo}_{hi}.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        for p in sel:
            w.writerow(row(p, "Instagram"))
            w.writerow(row(p, "Facebook"))
    print(out, len(sel), "posts")


if __name__ == "__main__":
    main()
