import contextlib
import dataclasses
import datetime
import functools
import json
import os
import random
import string
from typing import Annotated

import cachetools
import sqlalchemy
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

SHORT_URL_CHARSET: str = string.ascii_letters + string.digits + "-."
DATABASE_URI: str = os.environ.get("DATABASE_URI") or "sqlite:///sqlite.db"
DATABASE_CONNECT_ARGS: dict = json.loads(
    os.environ.get("DATABASE_CONNECT_ARGS_JSON") or "{}"
)
BASE_URL: str = os.environ.get("BASE_URL") or "http://locahost:8000"
LISTEN_ADDRESS: str = os.environ.get("LISTEN_ADDRESS") or "127.0.0.1"
LISTEN_PORT: int = int(os.environ.get("LISTEN_PORT") or 8000)

engine = create_engine(DATABASE_URI, connect_args=DATABASE_CONNECT_ARGS)


class ShortURL(SQLModel, table=True):
    id: str = Field(primary_key=True)
    url: str = Field()
    created: datetime.datetime = Field(
        default_factory=functools.partial(datetime.datetime.now, tz=datetime.UTC)
    )

    @functools.cached_property
    def short_url(self):
        return f"{BASE_URL}/r/{self.id}"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI(lifespan=lifespan)


class MaxRetriesReached(Exception):
    pass


@dataclasses.dataclass
class DBOps:
    # TODO: make those functions asynchronous?
    session: Session

    TIMED_CACHE = cachetools.TTLCache(
        maxsize=10,  # might need adjusting with more usage
        ttl=10 * 60,  # 10 minutes
    )
    URL_CACHE = cachetools.LRUCache(maxsize=128)

    @cachetools.cachedmethod(
        cache=lambda self: self.TIMED_CACHE,
        # just return an empty key as the cached value does not depend on inputs
        key=lambda *a, **kw: ("count",),
    )
    def get_urls_count(self):
        return self.session.exec(select(sqlalchemy.func.count(ShortURL.id))).first()

    @cachetools.cachedmethod(
        cache=lambda self: self.TIMED_CACHE,
        # just return an empty key as the cached value does not depend on inputs
        key=lambda *_, **kw: ("random_id_length", kw.get("maxfill")),
    )
    def get_random_id_length(self, *, max_fill=0.3, min_length=3):
        count = self.get_urls_count()
        charset_len = len(SHORT_URL_CHARSET)
        cur_len = min_length
        cur_combinations = charset_len**cur_len
        while cur_combinations * max_fill < count:
            cur_len *= cur_len
            cur_combinations *= charset_len
        return cur_len

    def get_next_id(self):
        # TODO: not sure whether random.choice() is the most efficient implementation?
        return "".join(
            random.choice(SHORT_URL_CHARSET) for _ in range(self.get_random_id_length())
        )

    def make_url(self, url: str, max_retries: int = 5):
        retries = 0
        while True:
            try:
                with self.session.begin_nested():
                    short_url = ShortURL(id=self.get_next_id(), url=url)
                    self.session.add(short_url)
                    self.session.commit()
                # session.refresh(self) # not needed because nothing new is generated?
                return short_url
            except sqlalchemy.exc.IntegrityError as exc:
                if retries >= max_retries:
                    raise MaxRetriesReached() from exc
                self.session.rollback()
                retries += 1
                continue

    @cachetools.cachedmethod(cache=lambda self: self.URL_CACHE)
    def get_url(self, id: str) -> str | None:
        # TODO: could pull it from a (shared) cache service before hitting the database
        statement = select(ShortURL.url).where(ShortURL.id == id)
        return self.session.exec(statement).one_or_none()


class ShortenRequest(BaseModel):
    url: str


@app.post("/url/shorten")
async def url_shorten(request: ShortenRequest, session: SessionDep):
    """
    Given a URL, generate a short version of the URL that can be later resolved to the originally
    specified URL.
    """
    ops = DBOps(session)
    try:
        model = ops.make_url(url=request.url)
    except MaxRetriesReached:
        raise HTTPException(
            status_code=503,
            detail="Failed to generate short url, try again later",
        )
    return {"short_url": model.short_url}


class ResolveRequest(BaseModel):
    short_url: str


@app.get("/r/{short_url}")
async def url_resolve(short_url: str, session: SessionDep):
    """
    Return a redirect response for a valid shortened URL string.
    If the short URL is unknown, return an HTTP 404 response.
    """
    ops = DBOps(session)
    url = ops.get_url(id=short_url)
    if url is None:
        raise HTTPException(status_code=404, detail="Short url not found")
    return RedirectResponse(url)


@app.get("/")
async def index():
    return "Your URL Shortener is running!"


def main():
    uvicorn.run(
        app,
        host=LISTEN_ADDRESS,
        port=LISTEN_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
