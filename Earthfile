VERSION 0.6

FROM python:3.10
WORKDIR /code

ARG POETRY_INSTALL_COMMON="--no-interaction"

build:
    RUN pip install poetry
    ENV POETRY_VIRTUALENVS_IN_PROJECT=true

    COPY pyproject.toml poetry.lock README.rst .
    RUN poetry install --no-root --no-dev ${POETRY_INSTALL_COMMON}

    COPY --dir ibidem .
    RUN poetry install --no-dev ${POETRY_INSTALL_COMMON}

    SAVE ARTIFACT .venv
    SAVE ARTIFACT ibidem
    SAVE IMAGE --cache-hint

test:
    FROM +build
    COPY tests tests
    RUN poetry install ${POETRY_INSTALL_COMMON}
    RUN poetry run pytest --junit-xml=xunit.xml
    SAVE ARTIFACT ./xunit.xml AS LOCAL xunit.xml

docker:
    FROM python:3.10-slim
    WORKDIR /code

    BUILD +test
    COPY +build/ibidem ibidem
    COPY +build/.venv .venv
    CMD ["/code/.venv/bin/python", "-m", "ibidem.homely_mqtt"]

    # builtins must be declared
    ARG EARTHLY_GIT_PROJECT_NAME
    ARG EARTHLY_GIT_SHORT_HASH

    # Override from command-line on CI
    ARG main_image=ghcr.io/$EARTHLY_GIT_PROJECT_NAME
    ARG VERSION=$EARTHLY_GIT_SHORT_HASH

    SAVE IMAGE --push ${main_image}:${VERSION} ${main_image}:latest

manifests:
    FROM dinutac/jinja2docker:latest
    WORKDIR /manifests
    COPY deploy/* /templates

    # builtins must be declared
    ARG EARTHLY_GIT_PROJECT_NAME
    ARG EARTHLY_GIT_SHORT_HASH

    # Override from command-line on CI
    ARG main_image=ghcr.io/$EARTHLY_GIT_PROJECT_NAME
    ARG VERSION=$EARTHLY_GIT_SHORT_HASH

    RUN --entrypoint -- /templates/deployment.yaml.j2 /templates/variables.toml --format=toml > ./deploy.yaml
    SAVE ARTIFACT ./deploy.yaml AS LOCAL deploy.yaml

deploy:
    BUILD +test
    BUILD --platform=linux/amd64 --platform=linux/arm64 +docker
    BUILD +manifests
