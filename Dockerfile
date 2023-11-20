FROM python:3.12

WORKDIR /srv
RUN --mount=type=cache,target=/root/.cache pip install --upgrade pip-tools wheel
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache pip-sync

RUN mkdir -p static

COPY . .

ARG STATIC_URL
ENV STATIC_URL ${STATIC_URL:-/static/}
RUN STATIC_URL=${STATIC_URL} python -m manage collectstatic --no-input

EXPOSE 8001
ENV PYTHONUNBUFFERED 1