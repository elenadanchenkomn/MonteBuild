# montebuild.com — сайт и автоматический контент

- `site/` — сайт, который публикует Netlify (настройки в `netlify.toml`).
- `content/` — статьи (JSON), очередь тем `queue.json`, проверенные факты `facts.md`, список статей `posts.json`.
- `photos/` — свои фото и видео с объектов для статей и постов (инструкция в `photos/README.md`).
- `social/` — готовые картинки каруселей для Facebook/Instagram (на сайт не попадают).
- `tools/` — сборка статьи (`build_article.py`), подготовка фото (`prep_image.py`), карусели (`build_slides.py`).
- `GUIDE.md` — правила текстов, обязательны для автоматических задач.
- `.github/workflows/indexnow.yml` — после изменения сайта сообщает новые страницы в IndexNow (Яндекс, Bing).

Публикация: push в `main` → Netlify выкладывает `site/` автоматически.
Ручная публикация через Netlify Drop больше не нужна — она перезапишет сайт версией без новых статей.
