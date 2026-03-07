ARG PY_VERSION
FROM ghcr.io/mortenlj/mise-lib/python-builder:local AS build

FROM ghcr.io/mortenlj/mise-lib/python-${PY_VERSION}:latest AS docker
ENTRYPOINT ["python", "-m", "ibidem.homely_mqtt"]
