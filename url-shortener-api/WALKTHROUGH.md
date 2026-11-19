# Walkthrough (interview prep, delete before pushing if you want)

**What it is:** a REST API. You POST a long URL and get back a short code; visiting `/{code}` redirects you.

## Request flow
1. `POST /links` → FastAPI validates the body against `ShortenRequest` (Pydantic). `HttpUrl` rejects garbage URLs; the regex `pattern` on `custom_code` only allows letters, digits, `-`, `_`. Bad input gets an automatic **422**.
2. A code is generated and inserted. `code` is the **PRIMARY KEY**, so the database itself refuses duplicates and raises `IntegrityError`. Random codes retry up to 5 times; a taken custom code returns **409 Conflict**.
3. `GET /{code}` looks up the target, increments `clicks` with `clicks = clicks + 1` (done in SQL so it's atomic), and returns a **307 redirect**.

## Design decisions you should be able to defend
- **`secrets.choice` instead of `random`.** `random` is predictable; with `secrets`, someone can't guess other people's links.
- **Collision math.** 62 characters, 7 positions gives 62^7 ≈ 3.5 trillion codes. Collisions are rare, so a short retry loop is enough.
- **307 vs 301.** A 301 is cached permanently by browsers, so later clicks never reach the server and aren't counted. A 307 always comes back to us.
- **Dependency injection (`Depends(get_conn)`).** Each request gets its own DB connection, closed afterwards. Tests swap the DB path with `monkeypatch`.
- **Route order.** `/{code}` is declared last so it doesn't swallow `/links/...` or `/docs`.

## Likely interview questions
- *How would you scale this?* Move to Postgres, put Redis in front for hot lookups (reads far outnumber writes), and run several stateless API instances behind a load balancer.
- *How would you stop abuse?* Rate limit `POST /links` per IP (see the rate-limiter project!), and check URLs against a blocklist.
- *Why FastAPI?* Type hints drive the validation and the auto-generated OpenAPI docs, and it's fast.

## Exercise to make it yours
Add an optional `expires_at` field: store it, and return **410 Gone** after it passes.
