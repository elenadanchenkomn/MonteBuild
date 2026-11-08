"""Собирает страницу полного прайс-листа site/prajs-list/index.html.

Данные: content/price_list.json  ({"updated": "ГГГГ-ММ-ДД", "sections": [{"title", "items": [{"name", "unit", "price"}]}]}).
Шапка, меню, форма заявки и подвал берутся со страницы site/ceny/index.html, чтобы совпадать с сайтом.

Обновить цены: поправить content/price_list.json → python3 tools/build_price_page.py → push в main.
"""
import json, html, re, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "content/price_list.json").read_text(encoding="utf-8"))
SHELL = (ROOT / "site/ceny/index.html").read_text(encoding="utf-8")
OUT = ROOT / "site/prajs-list/index.html"
URL = "https://montebuild.com/prajs-list/"

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
d = datetime.date.fromisoformat(DATA["updated"])
updated_ru = f"{d.day} {MONTHS[d.month - 1]} {d.year}"
total = sum(len(s["items"]) for s in DATA["sections"])

TITLE = "Прайс-лист на ремонтные и отделочные работы в Батуми | MonteBuild"
DESC = (f"Полный прайс MonteBuild: {total} видов работ — демонтаж, штукатурка, малярные, плитка, полы, "
        "электрика, сантехника. Цены за работу в лари, замер бесплатно.")

def esc(s): return html.escape(str(s), quote=True)
def price(p): return f"от {p:,} ₾".replace(",", " ")

faq = [
    ("Цены в прайсе окончательные?", "Нет, это цены «от». Итоговая стоимость зависит от состояния поверхностей, объёма и сложности. Точную сумму считаем после бесплатного замера и фиксируем в договоре."),
    ("Входят ли материалы в стоимость?", "Нет, все цены указаны только за работу. Материалы оплачиваются отдельно: можем помочь их выбрать, закупить и доставить на объект или работать с материалами заказчика."),
    ("Как посчитать примерную стоимость ремонта?", "Умножьте объём каждой работы на цену из прайса. Площадь стен обычно в 2,5–3 раза больше площади пола. Для покраски стен есть онлайн-калькулятор, а точную смету пришлём после замера."),
]

ld = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": "https://montebuild.com/"},
            {"@type": "ListItem", "position": 2, "name": "Цены", "item": "https://montebuild.com/ceny/"},
            {"@type": "ListItem", "position": 3, "name": "Прайс-лист", "item": URL}]},
        {"@type": "OfferCatalog", "name": "Прайс-лист MonteBuild на ремонтные работы", "url": URL,
         "itemListElement": [
             {"@type": "OfferCatalog", "name": s["title"], "itemListElement": [
                 {"@type": "Offer", "itemOffered": {"@type": "Service", "name": i["name"]},
                  "priceSpecification": {"@type": "UnitPriceSpecification", "minPrice": i["price"], "priceCurrency": "GEL", "unitText": i["unit"]},
                  "seller": {"@id": "https://montebuild.com/#business"}}
                 for i in s["items"]]}
             for s in DATA["sections"]]},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
    ]}

# --- head: берём со страницы /ceny/ и меняем мета-данные ---
head = SHELL.split("<body>", 1)[0]
head = re.sub(r"<title>.*?</title>", f"<title>{esc(TITLE)}</title>", head)
head = re.sub(r'(<meta (?:name="description"|property="og:description") content=")[^"]*', lambda m: m.group(1) + esc(DESC), head)
head = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + esc(TITLE), head)
head = head.replace("https://montebuild.com/ceny/", URL)
head = re.sub(r'<script type="application/ld\+json">.*?</script>',
              '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>", head, flags=re.S)

body_start, rest = SHELL.split('<main id="main">', 1)
body_start = body_start.split("<body>", 1)[1]
form_and_footer = '<section class="band band-dark" id="zayavka">' + rest.split('<section class="band band-dark" id="zayavka">', 1)[1]

toc = "".join(f'<li><a href="#r{n}">{esc(s["title"])}</a></li>' for n, s in enumerate(DATA["sections"], 1))
tables = []
for n, s in enumerate(DATA["sections"], 1):
    rows = "".join(f"<tr><th scope='row'>{esc(i['name'])}</th><td>{esc(i['unit'])}</td><td>{price(i['price'])}</td></tr>" for i in s["items"])
    tables.append(f'<h2 class="mt" id="r{n}">{esc(s["title"])}</h2>'
                  f'<div class="table-scroll"><table class="ptable"><thead><tr><th scope="col">Работа</th>'
                  f'<th scope="col">Единица</th><th scope="col">Цена работы</th></tr></thead><tbody>{rows}</tbody></table></div>')

faq_html = "".join(f"<details><summary><h3>{esc(q)}</h3></summary><p>{esc(a)}</p></details>" for q, a in faq)

main = f'''<main id="main">
<nav class="crumbs wrap" aria-label="Навигационная цепочка"><a href="/">Главная</a> <span aria-hidden="true">/</span> <a href="/ceny/">Цены</a> <span aria-hidden="true">/</span> <span>Прайс-лист</span></nav>
<section class="page-hero wrap single"><div class="page-hero-text">
<h1>Прайс-лист на ремонтные и отделочные работы</h1>
<p class="lead">{total} видов работ в Батуми и Аджарии: от демонтажа до сантехники и кондиционеров. Цены указаны за работу, без материалов. Окончательную стоимость считаем после бесплатного замера и фиксируем в договоре.</p>
<p class="post-meta">Цены обновлены {updated_ru}</p>
</div></section>
<section class="band"><div class="wrap narrow">
<nav class="toc" aria-label="Разделы прайса"><ol>{toc}</ol></nav>
<p>Нужна только покраска стен? Посчитайте стоимость в <a href="/kalkulyator-pokraski/">калькуляторе покраски</a> или посмотрите <a href="/ceny/">цены на основные услуги</a>.</p>
{"".join(tables)}
</div></section>
<section class="band"><div class="wrap narrow"><h2>Частые вопросы</h2><div class="faq">{faq_html}</div></div></section>
'''

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(head + "<body>" + body_start + main + form_and_footer, encoding="utf-8")
print(f"OK: {OUT.relative_to(ROOT)} — {len(DATA['sections'])} разделов, {total} позиций")
