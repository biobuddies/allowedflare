FROM debian:bookworm-slim

# TODO assert C.UTF8 locale and PYTHONUNBUFFERED are set correctly
ENV PYTHONUNBUFFERED 1

SHELL ["/bin/bash", "-o", "errexit", "-o", "nounset", "-o", "pipefail", "-o", "xtrace", "-c"]

WORKDIR /srv

# Bind mount caused "EROFS: read-only file system, open '/srv/package-lock.json'"
COPY package-lock.json ./

# Not using /srv/.venv yet because it would make volume-mounting /srv harder
# TODO: switch to watch.action=sync with ignore
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_SYSTEM_PYTHON=1

# hadolint ignore=DL3008, DL3013, DL3042, DL4006, SC2046, SC2239
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=bind,source=.biobuddies/includes.bash,target=.biobuddies/includes.bash \
    --mount=type=cache,target=/root/.npm \
    --mount=type=bind,source=package.json,target=package.json \
    --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    rm /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/99cache; \
    echo dash dash/sh boolean false | debconf-set-selections; \
    DEBIAN_FRONTEND=noninteractive dpkg-reconfigure dash; \
    USER=root; \
    export USER; \
    # workaround pstools absence; expected to raise warning about null
    ps() { xargs -E '\0' <"/proc/$2/cmdline"; }; \
    export -f ps; \
    echo "covdebug USER=$USER"; \
    bash .biobuddies/includes.bash forceready; \
    rm -rf /var/lib/apt/lists/*;

COPY . ./

ARG STATIC_URL
ENV STATIC_URL ${STATIC_URL:-/static/}
# hadolint ignore=SC2239
RUN mkdir -p static; STATIC_URL=${STATIC_URL} python -m manage collectstatic --no-input

EXPOSE 8001
