# url-shortener-api

A small REST API for shortening URLs, built with **FastAPI** and **SQLite**. It supports custom short codes, click tracking and Docker deployment.

## Features

- `POST /links` creates a short link (random or custom code)
- `GET /{code}` redirects to the original URL and counts the click
- `GET /links/{code}` returns stats (target, created date, clicks)
- `DELETE /links/{code}` removes a link
- Input validation with Pydantic (rejects malformed URLs and unsafe codes)
- Codes generated with `secrets` so they can't be guessed
- Interactive API docs at `/docs` (generated automatically)

## Quick start

```bash
git clone https://github.com/kuncman/url-shortener-api.git
cd url-shortener-api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to try it in the browser.

```bash
curl -X POST localhost:8000/links -H "Content-Type: application/json" \
     -d '{"url": "https://github.com", "custom_code": "gh"}'
# {"code":"gh","target":"https://github.com/","created_at":"...","clicks":0}

curl -i localhost:8000/gh        # 307 redirect to github.com
curl localhost:8000/links/gh     # {"clicks": 1, ...}
```

### With Docker

```bash
docker build -t url-shortener .
docker run -p 8000:8000 -v shortener-data:/data url-shortener
```

## Tests

```bash
pytest
```

## Configuration

| Variable       | Default        | Description                 |
|----------------|----------------|-----------------------------|
| `SHORTENER_DB` | `shortener.db` | Path to the SQLite database |

## Roadmap

- Link expiration dates
- API keys / per-user links
- Rate limiting on link creation

## License

MIT
