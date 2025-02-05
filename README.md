# URL Shortener Take-Home Project

Welcome to the Pocket Worlds URL Shortener Take-Home Project! In this repository, we'd like you to demonstrate your
engineering skills by creating a small Python project that implements a URL Shortener web service.

This project will serve as the primary jumping off point for our technical interviews. We expect you to spend a
couple of hours building an MVP that meets the requirements in the Product Description. You are free to implement
your solution and modify the provided template in the way that makes the most sense to you, but make sure to
update the README accordingly so that it's clear how to run and test your project. During the interviews, you will
be asked to demo your solution and discuss the reasoning behind your implementation decisions and their trade-offs.
Be prepared to share your screen for live coding and problem-solving with your interviewers based on this discussion.

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

## Getting Started

This repository contains a URL Shortener web service written in Python 3.13
using the [FastAPI](https://fastapi.tiangolo.com/) framework.
The API endpoints can be found in `server.py`.

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

To run the web service in interactive mode, use the following command:

```shell
url-shortener
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

## Submission Guidelines

When you have completed the project, please follow these guidelines for submission:

1. [x] Commit and push your code to your GitHub repository.
2. [ ] Update this README with any additional instructions, notes, or explanations regarding your implementation, if
   necessary.
3. [ ] Provide clear instructions on how to:
    - [x] run your project
    - [ ] test your project
4. [x] Share the repository URL with the hiring team or interviewer.

## TODOs

- [ ] purge the README.md from unnecessary paragraphs

## Additional Information

Feel free to be creative in how you approach this project. Your solution will be evaluated based on code quality,
efficiency, and how well it meets the specified requirements. Be prepared to discuss the reasoning behind your
implementation decisions and their trade-offs.

Remember that this project is the basis for the technical interviews, which do include live coding. We will not
ask you to solve an algorithm, but you will be expected to demo your solution and explain your thought process.

Good luck, and we look forward to seeing your URL Shortener project! If you have any questions or need
clarifications, please reach out to us.
