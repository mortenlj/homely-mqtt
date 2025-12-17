VERSION 0.7

IMPORT github.com/mortenlj/earthly-lib/kubernetes/commands AS lib-k8s-commands

FROM busybox

deps:
    FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim
    ENV UV_COMPILE_BYTECODE=1
    ENV UV_LINK_MODE=copy

    # Disable Python downloads, because we want to use the system interpreter
    # across both images. If using a managed Python version, it needs to be
    # copied from the build image into the final image; see `standalone.Dockerfile`
    # for an example.
    ENV UV_PYTHON_DOWNLOADS=0

    WORKDIR /app

    COPY pyproject.toml uv.lock .
    RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --locked --no-install-project

    SAVE ARTIFACT .venv
    SAVE IMAGE --cache-hint

build:
    FROM +deps

    COPY --dir .prospector.yaml ibidem tests .
    RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --locked && \
        uv run black --check . && \
        uv run prospector && \
        uv run pytest --junit-xml=xunit.xml

    # Omit development dependencies
    ENV UV_NO_DEV=1
    RUN --mount=type=cache,target=/root/.cache/uv \
        uv sync --locked

    SAVE ARTIFACT ibidem
    SAVE ARTIFACT ./xunit.xml AS LOCAL xunit.xml
    SAVE IMAGE --cache-hint

test:
    LOCALLY
    RUN uv sync --locked && \
        uv run black --check . && \
        uv run prospector && \
        uv run pytest --junit-xml=xunit.xml

black:
    LOCALLY
    RUN uv sync --locked && \
        uv run black --check .

docker:
    FROM python:3.11-slim

    WORKDIR /app

    COPY --dir +deps/.venv .
    COPY --dir +build/ibidem .

    ENV PATH="/bin:/usr/bin:/usr/local/bin:/app/.venv/bin"

    CMD ["/app/.venv/bin/python", "-m", "ibidem.homely_mqtt"]

    # builtins must be declared
    ARG EARTHLY_GIT_PROJECT_NAME
    ARG EARTHLY_GIT_SHORT_HASH

    # Override from command-line on CI
    ARG main_image=ghcr.io/$EARTHLY_GIT_PROJECT_NAME
    ARG VERSION=$EARTHLY_GIT_SHORT_HASH

    SAVE IMAGE --push ${main_image}:${VERSION} ${main_image}:latest

manifests:
    # builtins must be declared
    ARG EARTHLY_GIT_PROJECT_NAME
    ARG EARTHLY_GIT_SHORT_HASH

    ARG main_image=ghcr.io/$EARTHLY_GIT_PROJECT_NAME
    ARG VERSION=$EARTHLY_GIT_SHORT_HASH
    DO lib-k8s-commands+ASSEMBLE_MANIFESTS --IMAGE=${main_image} --VERSION=${VERSION}

deploy:
    BUILD --platform=linux/amd64 +build  # Do an explicit build to generate test report
    BUILD --platform=linux/amd64 --platform=linux/arm64 +docker
    BUILD +manifests
