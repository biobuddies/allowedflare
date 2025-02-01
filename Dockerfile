FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# TODO assert C.UTF8 locale and PYTHONUNBUFFERED are set correctly
ENV PYTHONUNBUFFERED 1

WORKDIR /srv

# hadolint ignore=DL3008,SC2046
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=bind,source=includes.sh,target=includes.sh \
    set -euxo pipefail \
    && rm /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/99cache \
    && apt-get update \
    && apt-get install -qq --no-install-recommends --yes nodejs npm \
        $(sed -En "s/'$//; s/^PACKAGES='//p" includes.sh) \
    && rm -rf /var/lib/apt/lists/*

# Bind mount caused "EROFS: read-only file system, open '/srv/package-lock.json'"
COPY package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=bind,source=package.json,target=package.json \
    npm install --frozen-lockfile

# Not using /srv/.venv because it would make volume-mounting /srv harder
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_SYSTEM_PYTHON=1
# hadolint ignore=DL3013,DL3042
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    uv pip sync --quiet requirements.txt

COPY . ./

ARG STATIC_URL
ENV STATIC_URL ${STATIC_URL:-/static/}
RUN mkdir -p static && STATIC_URL=${STATIC_URL} python -m manage collectstatic --no-input

EXPOSE 8001
