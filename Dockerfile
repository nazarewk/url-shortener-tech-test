FROM python:3.13-slim-bullseye

ENV LISTEN_ADDRESS=0.0.0.0
WORKDIR /app

COPY requirements.lock.txt /app
RUN pip install --no-cache -r /app/requirements.lock.txt

COPY server.py /app

ENTRYPOINT ["python", "server.py"]
