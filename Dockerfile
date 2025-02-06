FROM python:3.13-slim-bullseye

ENV LISTEN_ADDRESS=0.0.0.0
WORKDIR /app

COPY requirements.lock.txt /app
RUN pip install --no-cache -r /app/requirements.lock.txt

COPY url_shortener.py /app

ENTRYPOINT ["python", "url_shortener.py"]
