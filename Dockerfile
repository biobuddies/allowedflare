FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# TODO assert C.UTF8 and PYTHONUNBUFFERED are set correctly

WORKDIR /srv

COPY includes.sh ./
# hadolint ignore=DL3008,SC2046
RUN --mount=type=cache,target=/var/cache/apt \
    rm /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/99cache \
    && apt-get update \
    && apt-get install --no-install-recommends --quiet --quiet --yes nodejs npm \
        $(sed -En 's/"$//; s/^PACKAGES="//p' includes.sh) \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install --frozen-lockfile

COPY requirements.txt ./
# hadolint ignore=DL3013,DL3042
RUN --mount=type=cache,target=/root/.cache \
    uv venv /venv \
    && /venv/bin/uv pip sync --quiet requirements.txt

ENV PATH="/venv/bin:$PATH"

RUN mkdir -p static

COPY . ./

ARG STATIC_URL
ENV STATIC_URL ${STATIC_URL:-/static/}
RUN STATIC_URL=${STATIC_URL} python -m manage collectstatic --no-input

EXPOSE 8001
ENV PYTHONUNBUFFERED 1
