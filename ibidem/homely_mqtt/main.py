#!/usr/bin/env python
import logging
import signal
import sys

import uvicorn
from fastapi import FastAPI
from fiaas_logging import init_logging

from ibidem.homely_mqtt.config import settings
from ibidem.homely_mqtt.probes import router as probe_router
from ibidem.homely_mqtt.subsystems import manager

LOG = logging.getLogger(__name__)

app = FastAPI(title="Homely MQTT bridge", openapi_url=None)
app.include_router(probe_router, prefix="/_")


class ExitOnSignal(Exception):
    pass


def main():
    _init_logging(settings.debug)
    exit_code = 0
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, signal_handler)
    try:
        LOG.info("Starting homely-mqtt")
        uvicorn.run(
            "ibidem.homely_mqtt.main:app",
            host=settings.bind_address,
            port=settings.port,
            log_config=None,
            reload=settings.debug,
            access_log=settings.debug,
        )
    except ExitOnSignal:
        pass
    except Exception as e:
        logging.exception(f"unwanted exception: {e}")
        exit_code = 113
    return exit_code


def signal_handler(signum, frame):
    raise ExitOnSignal()


def _init_logging(debug):
    init_logging(debug=debug)
    return logging.getLogger().getEffectiveLevel()


@app.on_event("startup")
def launch_subsystems():
    manager.launch()


if __name__ == "__main__":
    sys.exit(main())
