#!/usr/bin/env python3
"""Сборка статьи блога montebuild.com из JSON и обновление всех связанных страниц.

Использование:
    python3 tools/build_article.py content/articles/<slug>.json
    python3 tools/build_article.py --refresh      # только пересобрать списки (блог, услуги, sitemap, llms.txt)

Формат content/articles/<slug>.json:
{
  "slug": "plesen-v-kvartire-batumi",              # латиница, из главного запроса
  "seo_title": "Плесень в квартире в Батуми: ... | MonteBuild",   # до ~65 символов без « | MonteBuild»
  "h1": "Плесень на стенах в Батуми: почему возвращается и как убрать",
  "description": "140–160 символов, с конкретикой",
  "date_published": "2026-11-09",
  "date_modified": "2026-11-09",
  "rubric": "vlaga",            # vlaga | dengi | standarty | keisy | investoram | diy
  "service": "/udalenie-pleseni/",                  # главная страница услуги (обратная ссылка)
  "services": ["/udalenie-pleseni/", "/malyarnye-raboty/", "/remont-pod-klyuch/"],  # блок «Услуги по теме», 2–3
  "hero": {"src": "assets/blog/plesen-v-kvartire-batumi-1.webp", "alt": "...", "w": 1280, "h": 960},
  "short": "Ответ на главный вопрос в 2–4 предложениях (блок «Коротко»).",
  "sections": [ {"id": "pochemu", "h2": "Почему ...?", "html": "<p>...</p>"} ],
  "faq": [ {"q": "Вопрос?", "a": "Ответ простым текстом."} ],        # 4–6 штук
  "cta": {"title": "Посчитаем ваш ремонт.", "text": "Пришлите ... в WhatsApp — ..."},
  "sources": [ {"title": "Название источника (месяц год)", "url": "https://..."} ],
  "sources_note": "Данные приведены по состоянию на дату публикации. Цены MonteBuild — за работу, без материалов.",
  "llms_summary": "1–3 предложения для llms.txt (по умолчанию = short)"
}
Пути картинок — от корня site/ (assets/...). Рядом с .webp должен лежать .jpg с тем же именем (для og:image).
"""
import html
import json
import math
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
POSTS = ROOT / "content" / "posts.json"
TEMPLATE = ROOT / "tools" / "templates" / "article-base.html"
BASE = "https://montebuild.com"
WA = "995595019615"
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
          "сентября", "октября", "ноября", "декабря"]
SERVICE_NAMES = {
    "/malyarnye-raboty/": "Малярные работы Q2–Q4",
    "/venecianskaya-shtukaturka/": "Венецианская штукатурка",
    "/dekorativnaya-shtukaturka/": "Декоративная штукатурка",
    "/elektroprovodka/": "Электропроводка",
    "/udalenie-pleseni/": "Удаление плесени",
    "/remont-pod-klyuch/": "Отделка под ключ",
    "/equipment-rental/": "Аренда оборудования",
    "/kalkulyator-pokraski/": "Калькулятор покраски",
    "/ceny/": "Цены",
    "/portfolio/": "Портфолио",
    "/kontakty/": "Контакты",
}
# страницы, на которых показывается блок «Статьи по теме»
RELATED_PAGES = ["/malyarnye-raboty/", "/venecianskaya-shtukaturka/", "/dekorativnaya-shtukaturka/",
                 "/elektroprovodka/", "/udalenie-pleseni/", "/remont-pod-klyuch/", "/equipment-rental/",
                 "/ceny/", "/kalkulyator-pokraski/", "/portfolio/"]
REL_START, REL_END = "<!-- blog-related:start -->", "<!-- blog-related:end -->"

esc = lambda s: html.escape(s, quote=True)


def ru_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def text_of(fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def read_minutes(a):
    words = len(text_of(a["short"] + " " + " ".join(s["html"] for s in a["sections"]) +
                        " " + " ".join(f["q"] + " " + f["a"] for f in a.get("faq", []))).split())
    return max(1, math.ceil(words / 180)), words


def wa_link(text):
    return f"https://wa.me/{WA}?text=" + urllib.parse.quote(text, safe="")


def template_parts():
    t = TEMPLATE.read_text(encoding="utf-8")
    head_tail = t[t.index('<meta name="geo.region"'):t.index('<script type="application/ld+json">')]
    ld = json.loads(t[t.index('<script type="application/ld+json">') + 35:t.index("</script>", t.index("ld+json"))])
    business = ld["@graph"][0]
    body_top = t[t.index("<body>"):t.index('<main id="main">') + len('<main id="main">')]
    body_bottom = t[t.index('<section class="band band-dark" id="zayavka">'):]
    return head_tail, business, body_top, body_bottom


def card(p, prefix):
    img = p["img"]
    return (f'<article class="post-card"><a href="/blog/{p["slug"]}/"><img src="{prefix}{img["src"]}" alt="{esc(img["alt"])}" '
            f'width="{img["w"]}" height="{img["h"]}" loading="lazy" decoding="async"></a>\n'
            f'<div><p class="post-meta">{ru_date(p["date"])} · {p["read_min"]} мин чтения</p>\n'
            f'<h3><a href="/blog/{p["slug"]}/">{esc(p["title"])}</a></h3><p>{esc(p["description"])}</p></div></article>')


def load_posts():
    return json.loads(POSTS.read_text(encoding="utf-8")) if POSTS.exists() else []


def save_posts(posts):
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    POSTS.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pick_related(posts, a, n=2):
    others = [p for p in posts if p["slug"] != a["slug"]]
    same = [p for p in others if p.get("rubric") == a.get("rubric") or p.get("service") == a.get("service")]
    rest = [p for p in others if p not in same]
    return (same + rest)[:n]


def render_article(a, posts):
    head_tail, business, body_top, body_bottom = template_parts()
    url = f"{BASE}/blog/{a['slug']}/"
    mins, words = read_minutes(a)
    hero = a["hero"]
    og_img = BASE + "/" + re.sub(r"\.webp$", ".jpg", hero["src"])
    if not (SITE / re.sub(r"\.webp$", ".jpg", hero["src"])).exists():
        og_img = BASE + "/" + hero["src"]
    faq = a.get("faq", [])
    graph = [business,
             {"@type": "BreadcrumbList", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Главная", "item": BASE + "/"},
                 {"@type": "ListItem", "position": 2, "name": "Блог", "item": BASE + "/blog/"},
                 {"@type": "ListItem", "position": 3, "name": a["h1"], "item": url}]},
             {"@type": "BlogPosting", "@id": url + "#article", "headline": a["h1"], "description": a["description"],
              "datePublished": a["date_published"], "dateModified": a["date_modified"], "inLanguage": "ru",
              "image": og_img, "mainEntityOfPage": url, "wordCount": words,
              "author": {"@type": "Organization", "name": "MonteBuild", "url": BASE + "/"},
              "publisher": {"@id": BASE + "/#business"}, "isPartOf": {"@id": BASE + "/blog/#blog"},
              "about": {"@id": BASE + a["service"]},
              "citation": [s["url"] for s in a.get("sources", [])]}]
    if faq:
        graph.append({"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]})
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    title = a["seo_title"]
    head = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(a['description'])}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="alternate" hreflang="ru" href="{url}">
<link rel="alternate" hreflang="x-default" href="{url}">
<meta property="og:type" content="article">
<meta property="article:published_time" content="{a['date_published']}">
<meta property="article:modified_time" content="{a['date_modified']}">
<meta property="og:site_name" content="MonteBuild">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(a['description'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
{head_tail}<script type="application/ld+json">{ld}</script>
</head>
"""
    toc = "".join(f'<li><a href="#{s["id"]}">{esc(s["h2"])}</a></li>' for s in a["sections"])
    if faq:
        toc += '<li><a href="#voprosy">Частые вопросы</a></li>'
    secs = "\n\n".join(f'<h2 id="{s["id"]}">{esc(s["h2"])}</h2>\n{s["html"].strip()}' for s in a["sections"])
    faq_html = ""
    if faq:
        faq_html = '\n\n<h2 id="voprosy">Частые вопросы</h2>\n<div class="faq">' + "".join(
            f'<details><summary><h3>{esc(f["q"])}</h3></summary><p>{esc(f["a"])}</p></details>' for f in faq) + "</div>"
    cta = a.get("cta") or {"title": "Посчитаем ваш ремонт.",
                           "text": "Пришлите площадь и фото квартиры в WhatsApp — ответим со сметой после бесплатного замера."}
    wa = wa_link(f"Здравствуйте! Прочитал статью «{a['h1']}». Хочу рассчитать ремонт.")
    sources = ""
    if a.get("sources"):
        sources = ('<section class="sources"><h2>Источники</h2><ol>' + "".join(
            f'<li><a href="{esc(s["url"])}" rel="noopener nofollow">{esc(s["title"])}</a></li>' for s in a["sources"]) +
            f'</ol>\n<p>{esc(a.get("sources_note", "Данные приведены по состоянию на дату публикации статьи. Цены MonteBuild указаны за работу, без материалов."))}</p></section>')
    modified = ""
    if a["date_modified"] != a["date_published"]:
        modified = f' · обновлено <time datetime="{a["date_modified"]}">{ru_date(a["date_modified"])}</time>'
    svc = "".join(f'<a class="svc" href="{s}"><h3>{esc(SERVICE_NAMES.get(s, s))}</h3></a>' for s in a["services"])
    related = "".join(card(p, "../../") for p in pick_related(posts, a))
    related_html = (f'<section class="band"><div class="wrap"><h2>Читайте также</h2><div class="post-grid">{related}</div></div></section>\n'
                    if related else "")
    body = f"""{body_top}
<nav class="crumbs wrap" aria-label="Навигационная цепочка"><a href="/">Главная</a> <span aria-hidden="true">/</span> <a href="/blog/">Блог</a> <span aria-hidden="true">/</span> <span>{esc(a['h1'])}</span></nav>
<article class="post wrap">
<header class="post-head">
<h1>{esc(a['h1'])}</h1>
<p class="post-meta">MonteBuild · <time datetime="{a['date_published']}">{ru_date(a['date_published'])}</time>{modified} · {mins} мин чтения</p>
</header>
<figure class="post-img"><img src="../../{hero['src']}" alt="{esc(hero['alt'])}" width="{hero['w']}" height="{hero['h']}" fetchpriority="high"></figure>
<div class="post-body">
<aside class="short"><p class="short-h">Коротко</p><p>{esc(a['short'])}</p></aside>
<nav class="toc" aria-label="Содержание"><p class="short-h">Содержание</p><ol>{toc}</ol></nav>

{secs}{faq_html}

<aside class="post-cta"><p><strong>{esc(cta['title'])}</strong> {esc(cta['text'])}</p>
<a class="btn btn-green" href="{wa}">Написать в WhatsApp</a></aside>
{sources}
</div>
</article>
<section class="band band-soft"><div class="wrap"><h2>Услуги по теме</h2><div class="svc-grid">{svc}</div></div></section>
{related_html}{body_bottom}"""
    return head + body, mins


def refresh_blog_index(posts):
    f = SITE / "blog" / "index.html"
    s = f.read_text(encoding="utf-8")
    grid = "".join(card(p, "../") for p in posts)
    s = re.sub(r'(<section class="band"><div class="wrap"><div class="post-grid">).*?(</div></div></section>)',
               lambda m: m.group(1) + grid + m.group(2), s, count=1, flags=re.S)
    i = s.index('<script type="application/ld+json">') + 35
    j = s.index("</script>", i)
    ld = json.loads(s[i:j])
    for node in ld["@graph"]:
        if node.get("@type") == "Blog":
            node["blogPost"] = [{"@type": "BlogPosting", "headline": p["title"], "url": f"{BASE}/blog/{p['slug']}/",
                                 "datePublished": p["date"]} for p in posts]
    s = s[:i] + json.dumps(ld, ensure_ascii=False) + s[j:]
    f.write_text(s, encoding="utf-8")


def refresh_service_pages(posts):
    changed = []
    for page in RELATED_PAGES:
        f = SITE / page.strip("/") / "index.html"
        if not f.exists():
            continue
        s = f.read_text(encoding="utf-8")
        mine = [p for p in posts if p.get("service") == page or page in p.get("services", [])][:3]
        block = ""
        if mine:
            block = (f'{REL_START}<section class="band"><div class="wrap"><h2>Статьи по теме</h2><div class="post-grid">' +
                     "".join(card(p, "../") for p in mine) + f'</div></div></section>\n{REL_END}\n')
        if REL_START in s:
            new = re.sub(re.escape(REL_START) + r".*?" + re.escape(REL_END) + r"\n?", block, s, flags=re.S)
        elif block:
            anchor = '<section class="band band-dark" id="zayavka">'
            if anchor not in s:
                continue
            new = s.replace(anchor, block + anchor, 1)
        else:
            new = s
        if new != s:
            f.write_text(new, encoding="utf-8")
            changed.append(page)
    return changed


def refresh_sitemap(posts, touched, today):
    f = SITE / "sitemap.xml"
    s = f.read_text(encoding="utf-8")
    urls = dict(re.findall(r"<url>\s*<loc>([^<]+)</loc>(.*?)</url>", s, flags=re.S))
    order = re.findall(r"<loc>([^<]+)</loc>", s)

    def entry(loc, lastmod, prio):
        return f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <priority>{prio}</priority>\n  </url>\n"

    out = {}
    for loc in order:
        body = urls[loc]
        lm = re.search(r"<lastmod>([^<]+)</lastmod>", body)
        pr = re.search(r"<priority>([^<]+)</priority>", body)
        out[loc] = [lm.group(1) if lm else today, pr.group(1) if pr else "0.6"]
    for p in posts:
        loc = f"{BASE}/blog/{p['slug']}/"
        if loc not in out:
            out[loc] = [p["modified"], "0.6"]
            order.append(loc)
        else:
            out[loc][0] = max(out[loc][0], p["modified"])
    for page in touched:
        loc = BASE + page
        if loc in out:
            out[loc][0] = max(out[loc][0], today)
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join(entry(loc, *out[loc]) for loc in order) + "</urlset>\n"
    f.write_text(xml, encoding="utf-8")


def refresh_llms(posts):
    f = SITE / "llms.txt"
    s = f.read_text(encoding="utf-8")
    lines = "".join(f"- [{p['title']}]({BASE}/blog/{p['slug']}/): {p['summary']}\n" for p in posts)
    s = re.sub(r"(## Статьи\n\n)(?:- \[.*\n)*", lambda m: m.group(1) + lines, s, count=1)
    f.write_text(s, encoding="utf-8")


def check_article(a):
    problems = []
    for k in ["slug", "seo_title", "h1", "description", "date_published", "date_modified", "service", "services",
              "hero", "short", "sections"]:
        if not a.get(k):
            problems.append(f"нет поля {k}")
    if not re.fullmatch(r"[a-z0-9-]+", a.get("slug", "")):
        problems.append("slug — только латиница, цифры и дефис")
    if len(a.get("description", "")) > 170:
        problems.append(f"description длиннее 170 символов ({len(a['description'])})")
    if len(a.get("seo_title", "").replace(" | MonteBuild", "")) > 70:
        problems.append("seo_title длиннее 70 символов без « | MonteBuild»")
    if not (SITE / a.get("hero", {}).get("src", "x")).exists():
        problems.append(f"нет файла картинки site/{a.get('hero', {}).get('src')}")
    ids = [s["id"] for s in a.get("sections", [])]
    if len(ids) != len(set(ids)):
        problems.append("повторяются id разделов")
    body = " ".join(s["html"] for s in a.get("sections", []))
    if a.get("service") and f'href="{a["service"]}' not in body:
        problems.append(f"в тексте нет ссылки на главную услугу {a['service']}")
    for href in re.findall(r'href="(/[^"#]*)', body):
        path = SITE / href.strip("/") / "index.html" if href != "/" else SITE / "index.html"
        if not path.exists():
            problems.append(f"битая внутренняя ссылка {href}")
    return problems


def main():
    import datetime
    today = datetime.date.today().isoformat()
    posts = load_posts()
    if sys.argv[1:] == ["--refresh"]:
        a = None
    else:
        a = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        problems = check_article(a)
        if problems:
            print("ОШИБКИ:\n- " + "\n- ".join(problems))
            sys.exit(1)
        page, mins = render_article(a, posts)
        out = SITE / "blog" / a["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        entry = {"slug": a["slug"], "title": a["h1"], "description": a["description"], "date": a["date_published"],
                 "modified": a["date_modified"], "read_min": mins, "rubric": a.get("rubric", ""),
                 "service": a["service"], "services": a["services"],
                 "img": {"src": a["hero"]["src"], "alt": a["hero"]["alt"], "w": a["hero"]["w"], "h": a["hero"]["h"]},
                 "summary": a.get("llms_summary") or a["short"]}
        posts = [p for p in posts if p["slug"] != a["slug"]] + [entry]
        save_posts(posts)
        posts = load_posts()
        # пересобрать страницу уже с актуальным списком «Читайте также»
        page, mins = render_article(a, posts)
        out.write_text(page, encoding="utf-8")
        print(f"Статья: site/blog/{a['slug']}/index.html ({mins} мин чтения)")
    refresh_blog_index(posts)
    touched = refresh_service_pages(posts) + ["/blog/"]
    refresh_sitemap(posts, touched, today)
    refresh_llms(posts)
    print("Обновлено: /blog/, sitemap.xml, llms.txt; блок «Статьи по теме»:", ", ".join(touched[:-1]) or "без изменений")
    if a:
        print("URL:", f"{BASE}/blog/{a['slug']}/")


if __name__ == "__main__":
    main()
