# URL Shortener Take-Home Project

## Project Description

Using the provided Python project template, your task is to implement a URL Shortener web service that exposes
the following API endpoints:

* POST `/url/shorten`: accepts a URL to shorten (e.g. https://www.google.com) and returns a short URL that
  can be resolved at a later time (e.g. http://localhost:8000/r/abc)
* GET `r/<short_url>`: resolve the given short URL (e.g. http://localhost:8000/r/abc) to its original URL
  (e.g. https://www.google.com). If the short URL is unknown, an HTTP 404 response is returned.

Your solution must support running the URL shortener service with multiple workers.

For example, it should be possible to start two instances of the service, make a request to shorten a URL
to one instance, and be able to resolve that shortened URL by sending subsequent requests to the second instance.

## Design

The project is written in Python 3.13 using [FastAPI](https://fastapi.tiangolo.com/) framework:

- the project is contained in a single Python file `server.py`, the list of supported URLs
  can be found near the bottom of it,
- stores short URLs inside SQL database supported by [SQLModel](https://sqlmodel.tiangolo.com/),
    - currently uses synchronous SQL, but is expected to switch to asynchronous SQL queries
- uses a local in-memory TTL & LRU caches backed by [cachetools](https://cachetools.readthedocs.io),
    - it is expected to be extended with external shared cache (like memcached, redis) to reduce
      single instance's/worker's memory usage and aid scalability,

### Short URL generation design

I have decided to go with random instead of sequential (with a predictably shuffled alphabet) generation:

- it does not require synchronization between workers,
- it does not require rehashing the whole database upon changing approach in the future,
- conflicts are detected by a database integrity mechanisms,
- conflicts are not expected to happen many times in a row, because the "address space" size is automatically
  adjusted upon filling up,

#### Short URL generation implementation

Short URLs are randomly generated `X`-character strings:

- short url is used as a database primary key `id`
- the alphabet is: lower- & uppercase letters, digits and `-.` (dash and dot),
- the string length `X` is automatically calculated while database grows:
    - starts at `3` characters
    - is increased by `1` whenever more than `Y` (`0.3` by default) of the available generation space is filled
- conflicts are detected through database integrity errors:
    - generated in a nested transaction
    - upon failure rollbacks the nested transaction and tries again
    - it is retried up to `R` (`5` by default) times before `503 Failed to generate short url, try again later`

Maximum generation space filling `Y` and maximum retries number `R` are basic mechanisms to aid scaling of the solution.

Default implementation uses a shared local sqlite database, it needs to be switched to more advanced SQL engine
when moving to production (MySQL, Postrgres etc.).

Those engines should be sufficiently tunable for faster verification of uniqueness upon creation and retrieval of
entries by tuning indices.

### Short URL retrieval

Short URLs are retrieved by their primary keys in following order:

1. (to be implemented) from a shared/distributed cache, which can be scaled a lot more easily than an SQL database
2. small local in-memory cache
3. as the only field pulled in from the database

## Getting Started

To begin the project, clone the repository to your local machine:

```shell
git clone https://github.com/nazarewk/url-shortener-tech-test.git
```

To set up a local Linux/MacOS/WSL development environment:

1. install [`direnv`](https://direnv.net/docs/installation.html)
2. install [`lix`](https://lix.systems/install/#on-any-other-linuxmacos-system) (or other Nix implementation)
3. enter repository root and run `direnv allow`
    - now you can find all available executables in your `$PATH` and in `.bin/` subdirectory
    - there is `.bin/python` that you can point your IDE to (instead of managing virtualenv yourself)
    - there is `url-shortener` shortcut to run the `server.py` directly during development

To pick up changes to your development environment (`*.nix` files or `requirements.txt`), just run `direnv reload` or
restart your terminal.

### Running the service

To run the web service in interactive mode, use any of the following commands at the root of the repository:

```shell
url-shortener
python server.py
./.bin/python server.py
```

You can run the production version of the application with any of those commands:

```shell
# locally
nix run '.#url-shortener'
# from the default branch
nix run 'github.com:nazarewk/url-shortener-tech-test#url-shortener'
# from specific commit
nix run 'github.com:nazarewk/url-shortener-tech-test/<commit-id>#url-shortener'
nix run 'github.com:nazarewk/url-shortener-tech-test#url-shortener'
# from specific branch
nix run 'github.com:nazarewk/url-shortener-tech-test/<branch-name>#url-shortener'
# from specific tag
nix run 'github.com:nazarewk/url-shortener-tech-test/<tag>#url-shortener'

```

You can build a release container image (`pw/url-shortener:latest`)
and load it into your `podman` (or `docker`) with this command:

```shell
podman load --input="$(nix build '.#url-shortener.container' --no-link --print-out-paths)"
```

Then you can run it with:

```shell
podman run -it --rm -p 8000:8000/tcp --name url-shortener pw/url-shortener:latest
```

By default, the web service will run on port 8000.

### Testing

Swagger UI is available as part of the FastAPI framework that can be used to inspect and test
the API endpoints of the URL shortener. To access it, start run the web service and go to http://localhost:8000/docs

Alternatively you can call the endpoint using `curl` or your favorite HTTP client:

```shell
curl http://localhost:8000/url/shorten -XPOST -H 'Content-Type: application/json' -d '{"url":"https://example.com"}'
# <copy the URL from results>
curl -v http://127.0.0.1:8000/r/<short-url>
# you should see `location: https://example.com` near the end of output
```

## Submission Guidelines

When you have completed the project, please follow these guidelines for submission:

1. [x] Commit and push your code to your GitHub repository.
2. [x] Update this README with any additional instructions, notes, or explanations regarding your implementation, if
   necessary.
3. [x] Provide clear instructions on how to:
    - [x] run your project
    - [x] test your project
4. [x] Share the repository URL with the hiring team or interviewer.

## TODOs

- [ ] confirm it works with multiple workers and separate instances

