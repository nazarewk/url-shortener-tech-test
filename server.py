import contextlib
import datetime
import functools
import json
import os
import random
import string
from typing import Annotated

import sqlalchemy
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

DATABASE_URI: str = os.environ.get("DATABASE_URI") or "sqlite:///sqlite.db"
DATABASE_CONNECT_ARGS: dict = json.loads(
    os.environ.get("DATABASE_CONNECT_ARGS_JSON") or "{}"
)

BASE_URL: str = os.environ.get("BASE_URL") or "http://locahost:8000"
LISTEN_ADDRESS: str = os.environ.get("LISTEN_ADDRESS") or "127.0.0.1"
LISTEN_PORT: int = int(os.environ.get("LISTEN_PORT") or 8000)

engine = create_engine(DATABASE_URI, connect_args=DATABASE_CONNECT_ARGS)

charset: str = string.ascii_letters + string.digits + "-."


class ShortenRequest(BaseModel):
    url: str


class ShortURL(SQLModel, table=True):
    id: str = Field(primary_key=True)
    url: str = Field()
    created: datetime.datetime = Field(
        default_factory=functools.partial(datetime.datetime.now, tz=datetime.UTC)
    )

    @functools.cached_property
    def short_url(self):
        return f"{BASE_URL}/r/{self.id}"

    @classmethod
    def make(cls, session: Session, url: str, max_retries: int = 5):
        retries = 0
        while True:
            try:
                with session.begin_nested():
                    self = cls(id=get_next_id(session), url=url)
                    session.add(self)
                    session.commit()
                # session.refresh(self) # not needed because nothing new is generated?
                return self
            except sqlalchemy.exc.IntegrityError:
                if retries >= max_retries:
                    raise
                # TODO: can there be any other IntegrityError than PK uniqueness related in this case?
                session.rollback()
                retries += 1
                continue

    @classmethod
    def get(cls, session: Session, id: str):
        # TODO: try to pull it from cache before hitting the database?
        return session.get(ShortURL, id)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI(lifespan=lifespan)


def get_urls_count(session: Session):
    # TODO: make this cached for a reasonable amount of time?
    return session.exec(select(sqlalchemy.func.count(ShortURL.id))).first()


def get_random_id_length(session: Session, *, max_fill=0.3, min_length=4):
    # TODO: make this cached for a reasonable amount of time?
    count = get_urls_count(session)
    charset_len = len(charset)
    cur_len = min_length
    cur_combinations = charset_len**cur_len
    while cur_combinations * max_fill < count:
        cur_len *= cur_len
        cur_combinations *= charset_len
    return cur_len


def get_next_id(session: Session):
    # TODO: not sure whether random.choice() is the most efficient implementation?
    return "".join(random.choice(charset) for _ in range(get_random_id_length(session)))


@app.post("/url/shorten")
async def url_shorten(request: ShortenRequest, session: SessionDep):
    """
    Given a URL, generate a short version of the URL that can be later resolved to the originally
    specified URL.
    """
    model = ShortURL.make(
        session=session,
        url=request.url,
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
    model = ShortURL.get(session=session, id=short_url)
    if not model:
        raise HTTPException(status_code=404, detail="Short url not found")
    return RedirectResponse(model.url)


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
