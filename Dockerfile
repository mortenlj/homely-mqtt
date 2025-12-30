FROM ghcr.io/mortenlj/mise-lib/python-builder:latest AS build

FROM ghcr.io/mortenlj/mise-lib/python-3.11:latest AS docker
ENTRYPOINT ["python", "-m", "ibidem.homely_mqtt"]
