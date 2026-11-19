"""A minimal URL shortener API built with FastAPI and SQLite."""
from __future__ import annotations

import os
import secrets
import sqlite3
import string
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, HttpUrl

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 7
DB_PATH = os.environ.get("SHORTENER_DB", "shortener.db")


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            target TEXT NOT NULL,
            created_at TEXT NOT NULL,
            clicks INTEGER NOT NULL DEFAULT 0
        )"""
    )
    conn.commit()


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    conn.close()
    yield


app = FastAPI(title="URL Shortener", version="0.1.0", lifespan=lifespan)


class ShortenRequest(BaseModel):
    url: HttpUrl
    custom_code: str | None = Field(default=None, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")


class LinkOut(BaseModel):
    code: str
    target: str
    created_at: str
    clicks: int


def generate_code() -> str:
    # secrets (not random) so codes aren't predictable/enumerable.
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


@app.post("/links", response_model=LinkOut, status_code=201)
def create_link(body: ShortenRequest, conn: sqlite3.Connection = Depends(get_conn)):
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    target = str(body.url)
    if body.custom_code:
        candidates = [body.custom_code]
    else:
        candidates = [generate_code() for _ in range(5)]  # retry on rare collision

    for code in candidates:
        try:
            conn.execute(
                "INSERT INTO links (code, target, created_at) VALUES (?, ?, ?)", (code, target, created)
            )
            conn.commit()
            return LinkOut(code=code, target=target, created_at=created, clicks=0)
        except sqlite3.IntegrityError:
            continue
    if body.custom_code:
        raise HTTPException(409, "custom code already taken")
    raise HTTPException(500, "could not generate a unique code")


@app.get("/links/{code}", response_model=LinkOut)
def link_stats(code: str, conn: sqlite3.Connection = Depends(get_conn)):
    row = conn.execute("SELECT code, target, created_at, clicks FROM links WHERE code = ?", (code,)).fetchone()
    if not row:
        raise HTTPException(404, "link not found")
    return LinkOut(code=row[0], target=row[1], created_at=row[2], clicks=row[3])


@app.delete("/links/{code}", status_code=204)
def delete_link(code: str, conn: sqlite3.Connection = Depends(get_conn)):
    cur = conn.execute("DELETE FROM links WHERE code = ?", (code,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(404, "link not found")


@app.get("/{code}")
def redirect(code: str, conn: sqlite3.Connection = Depends(get_conn)):
    row = conn.execute("SELECT target FROM links WHERE code = ?", (code,)).fetchone()
    if not row:
        raise HTTPException(404, "link not found")
    conn.execute("UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,))
    conn.commit()
    return RedirectResponse(row[0], status_code=307)
