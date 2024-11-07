FROM python:3.12

# TODO assert C.UTF8 and PYTHONUNBUFFERED are set correctly

WORKDIR /srv

COPY includes.sh .
# hadolint ignore=SC2086
RUN --mount=type=cache,target=/var/cache/apt \
    rm /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/99cache \
    && source includes.sh \
    && apt-get update \
    && apt-get install --no-install-recommends --quiet --quiet --yes nodejs $PACKAGES \
    && rm -rf /var/lib/apt/lists/*

COPY package-lock.json .
RUN --mount=type=cache,target=/root/.npm \
    npm install --frozen-lockfile

COPY requirements.txt .
# hadolint ignore=DL3013,DL3042
RUN --mount=type=cache,target=/root/.cache \
    pip install --disable-pip-version-check --upgrade "$(grep ^uv requirements.txt)" \
    && uv venv \
    && uv pip sync requirements.txt

RUN mkdir -p static

COPY . .

ARG STATIC_URL
ENV STATIC_URL ${STATIC_URL:-/static/}
RUN STATIC_URL=${STATIC_URL} python -m manage collectstatic --no-input

EXPOSE 8001
ENV PYTHONUNBUFFERED 1
