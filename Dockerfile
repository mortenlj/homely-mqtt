FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS deps
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_NO_EDITABLE=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --locked --no-install-project

FROM deps AS build
COPY .prospector.yaml ./
COPY ibidem/ ./ibidem/
COPY tests/ ./tests/
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --locked && \
    find && \
	uv run black --check . && \
	uv run prospector && \
	uv run pytest --junit-xml=xunit.xml
ENV UV_NO_DEV=1
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --locked

FROM python:3.11-slim AS docker
WORKDIR /app
COPY --from=build /app/.venv/ ./.venv/
ENV PATH="/bin:/usr/bin:/usr/local/bin:/app/.venv/bin"
CMD ["/app/.venv/bin/python", "-m", "ibidem.homely_mqtt"]
