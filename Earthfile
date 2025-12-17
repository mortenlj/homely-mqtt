VERSION 0.7

IMPORT github.com/mortenlj/earthly-lib/kubernetes/commands AS lib-k8s-commands

FROM busybox

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

manifests:
    # builtins must be declared
    ARG EARTHLY_GIT_PROJECT_NAME
    ARG EARTHLY_GIT_SHORT_HASH

    ARG main_image=ghcr.io/$EARTHLY_GIT_PROJECT_NAME
    ARG VERSION=$EARTHLY_GIT_SHORT_HASH
    DO lib-k8s-commands+ASSEMBLE_MANIFESTS --IMAGE=${main_image} --VERSION=${VERSION}

deploy:
    BUILD +manifests
