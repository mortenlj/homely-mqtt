FROM jdxcode/mise:latest AS build
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_NO_EDITABLE=1
WORKDIR /app
COPY .config ./.config/
COPY mise.toml ./mise.toml
RUN mise trust -a && mise install
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --locked --no-install-project
COPY ibidem/ ./ibidem/
COPY tests/ ./tests/
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --locked
RUN mise run ci
ENV UV_NO_DEV=1
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --locked

FROM python:3.11-slim AS docker
WORKDIR /app
COPY --from=build /app/.venv/ ./.venv/
RUN ln --force --logical --symbolic --target-directory /app/.venv/bin /usr/local/bin/python*
ENV PATH="/app/.venv/bin:/bin:/usr/bin:/usr/local/bin"
RUN python -c "import ibidem.homely_mqtt" ## Minimal testing that imports actually work
ENTRYPOINT ["python", "-m", "ibidem.homely_mqtt"]
