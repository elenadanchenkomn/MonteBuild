#!/usr/bin/env python3
"""Публикация постов MonteBuild в Facebook и Instagram через Graph API Meta.

Запускается GitHub Actions (.github/workflows/social.yml) каждый час:
    python3 tools/publish_social.py publish   # опубликовать всё, чему пришло время
    python3 tools/publish_social.py check     # проверить доступ (токен, страница, Instagram), ничего не публикуя

Нужен секрет репозитория META_PAGE_TOKEN — постоянный токен системного пользователя портфолио «Твой мастер»
(или токен страницы) с доступом к странице MonteBuild (ID 135370676333010)
с правами pages_manage_posts, pages_read_engagement, pages_show_list, instagram_basic,
instagram_content_publish. Значение токена никогда не печатается.

Очередь — content/social_posts.json:
{
  "posts": [
    {
      "id": "2026-11-10-plesen",                       # уникальный
      "publish_at": "2026-11-10T19:00:00+04:00",       # когда публиковать (ISO с часовым поясом)
      "networks": ["facebook", "instagram"],
      "type": "carousel",                              # photo | carousel | reel
      "media": ["social/2026-11-10-plesen/slide-01.jpg", ...],   # пути в репозитории; для Instagram только JPEG, для reel — один mp4
      "caption_instagram": "текст для Instagram",
      "caption_facebook": "текст для Facebook (можно со ссылкой)",
      "link": "https://montebuild.com/blog/...",       # необязательно: для Facebook — пост-ссылка вместо фото, если type = link
      "status": "scheduled"                            # scheduled → published | error (заполняет скрипт)
    }
  ]
}
Скрипт дописывает в пост "result": {"facebook": {...}, "instagram": {...}} и "published_at".
Ошибка в одной сети не мешает другой; при повторном запуске уже опубликованная сеть не дублируется.
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "content" / "social_posts.json"
REPO = os.environ.get("GITHUB_REPOSITORY", "elenadanchenkomn/montebuild")
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
API = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v27.0")
TOKEN = os.environ.get("META_PAGE_TOKEN", "")


class GraphError(Exception):
    pass


def call(method, path, params=None):
    params = dict(params or {})
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path.lstrip('/')}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body).get("error", {})
            msg = f"{err.get('type')}: {err.get('message')} (code {err.get('code')}/{err.get('error_subcode')})"
        except Exception:
            msg = body[:300]
        raise GraphError(f"{method} {path} → HTTP {e.code}: {msg}") from None


PAGE_ID = os.environ.get("META_PAGE_ID", "135370676333010")  # страница MonteBuild


def accounts():
    """Токен может быть токеном страницы или системного пользователя бизнес-портфолио.
    Во втором случае берём из /me/accounts токен нужной страницы (он тоже не истекает)."""
    global TOKEN
    try:
        pages = call("GET", "me/accounts", {"fields": "id,name,access_token", "limit": "100"}).get("data", [])
    except GraphError:
        pages = []  # это уже токен страницы
    page = next((p for p in pages if p["id"] == PAGE_ID), None)
    if pages and not page:
        raise GraphError(f"у токена нет доступа к странице {PAGE_ID}; доступны: " + ", ".join(p["name"] for p in pages))
    if page:
        TOKEN = page["access_token"]
    me = call("GET", "me", {"fields": "id,name,instagram_business_account{id,username}"})
    ig = me.get("instagram_business_account") or {}
    return me["id"], me.get("name"), ig.get("id"), ig.get("username")


def media_url(path):
    return RAW + urllib.parse.quote(path)


def wait_container(cid, label, tries=60, delay=10):
    for _ in range(tries):
        st = call("GET", cid, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise GraphError(f"Instagram {label}: контейнер {code}: {st.get('status')}")
        time.sleep(delay)
    raise GraphError(f"Instagram {label}: обработка не закончилась за {tries * delay} с")


def publish_instagram(ig_id, post):
    caption = post.get("caption_instagram") or post.get("caption_facebook") or ""
    media = post["media"]
    kind = post["type"]
    if kind == "reel":
        c = call("POST", f"{ig_id}/media", {"media_type": "REELS", "video_url": media_url(media[0]),
                                            "caption": caption, "share_to_feed": "true"})
        wait_container(c["id"], "reel")
        cid = c["id"]
    elif kind == "carousel" and len(media) > 1:
        children = []
        for m in media[:10]:
            c = call("POST", f"{ig_id}/media", {"image_url": media_url(m), "is_carousel_item": "true"})
            wait_container(c["id"], "слайд", tries=30, delay=3)
            children.append(c["id"])
        c = call("POST", f"{ig_id}/media", {"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption})
        wait_container(c["id"], "карусель", tries=30, delay=3)
        cid = c["id"]
    else:
        c = call("POST", f"{ig_id}/media", {"image_url": media_url(media[0]), "caption": caption})
        wait_container(c["id"], "фото", tries=30, delay=3)
        cid = c["id"]
    res = call("POST", f"{ig_id}/media_publish", {"creation_id": cid})
    link = call("GET", res["id"], {"fields": "permalink"}).get("permalink")
    return {"id": res["id"], "permalink": link}


def publish_facebook(page_id, post):
    text = post.get("caption_facebook") or post.get("caption_instagram") or ""
    media = post.get("media", [])
    kind = post["type"]
    if kind == "reel":
        res = call("POST", f"{page_id}/videos", {"file_url": media_url(media[0]), "description": text})
        return {"id": res.get("id")}
    if kind == "link" or not media:
        res = call("POST", f"{page_id}/feed", {"message": text, "link": post.get("link", "")})
        return {"id": res.get("id")}
    if len(media) == 1:
        res = call("POST", f"{page_id}/photos", {"url": media_url(media[0]), "message": text})
        return {"id": res.get("post_id") or res.get("id")}
    ids = []
    for m in media[:10]:
        r = call("POST", f"{page_id}/photos", {"url": media_url(m), "published": "false"})
        ids.append(r["id"])
    params = {"message": text}
    for i, fid in enumerate(ids):
        params[f"attached_media[{i}]"] = json.dumps({"media_fbid": fid})
    res = call("POST", f"{page_id}/feed", params)
    return {"id": res.get("id")}


def now():
    return dt.datetime.now(dt.timezone.utc)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "publish"
    if not TOKEN:
        print("Нет секрета META_PAGE_TOKEN — публикация не настроена.")
        sys.exit(0 if mode == "publish" else 1)
    page_id, page_name, ig_id, ig_user = accounts()
    print(f"Страница: {page_name} ({page_id}); Instagram: @{ig_user or '—'} ({ig_id or 'не привязан'})")
    if mode == "check":
        perms = call("GET", "me", {"fields": "id"})  # токен рабочий, если дошли сюда
        print("Доступ работает." if perms.get("id") else "Странный ответ API")
        if not ig_id:
            print("ВНИМАНИЕ: к странице не привязан Instagram (бизнес-аккаунт или аккаунт автора).")
            sys.exit(1)
        return
    q = json.loads(QUEUE.read_text(encoding="utf-8")) if QUEUE.exists() else {"posts": []}
    changed, failures = False, []
    for post in q["posts"]:
        if post.get("status") not in ("scheduled", "error"):
            continue
        if post.get("attempts", 0) >= 3:
            continue
        when = dt.datetime.fromisoformat(post["publish_at"])
        if when > now():
            continue
        if now() - when > dt.timedelta(days=2):
            post["status"] = "error"
            post["error"] = "Пропущено: время публикации прошло больше 2 дней назад"
            changed = True
            continue
        result = post.setdefault("result", {})
        errors = {}
        for net in post["networks"]:
            if result.get(net, {}).get("id"):
                continue
            try:
                if net == "instagram":
                    if not ig_id:
                        raise GraphError("к странице не привязан Instagram")
                    result[net] = publish_instagram(ig_id, post)
                elif net == "facebook":
                    result[net] = publish_facebook(page_id, post)
                print(f"OK {post['id']} → {net}: {result[net]}")
            except GraphError as e:
                errors[net] = str(e)
                print(f"ОШИБКА {post['id']} → {net}: {e}")
        post["attempts"] = post.get("attempts", 0) + (1 if errors else 0)
        if errors:
            post["status"] = "error"
            post["error"] = errors
            failures.append(post["id"])
        else:
            post["status"] = "published"
            post["published_at"] = now().isoformat(timespec="seconds")
            post.pop("error", None)
        changed = True
    if changed:
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failures:
        print("Не опубликовано:", ", ".join(failures))
        sys.exit(1)


if __name__ == "__main__":
    main()
