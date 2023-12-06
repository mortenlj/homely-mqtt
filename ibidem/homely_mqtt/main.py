#!/usr/bin/env python
import logging
import signal
import sys
from queue import Queue

import uvicorn
from fastapi import FastAPI

from ibidem.homely_mqtt.config import settings
from ibidem.homely_mqtt.homely import Homely
from ibidem.homely_mqtt.logging import get_log_config
from ibidem.homely_mqtt.mqtt import MqttManager
from ibidem.homely_mqtt.probes import router as probe_router
from ibidem.homely_mqtt.subsystems import manager

LOG = logging.getLogger(__name__)
NOISY_LOGGERS = (
    "engineio.client",
    "socketio.client",
)

app = FastAPI(title="Homely MQTT bridge", openapi_url=None)
app.include_router(probe_router, prefix="/_")


class ExitOnSignal(Exception):
    pass


def main():
    log_level = logging.DEBUG if settings.debug else logging.INFO
    log_format = "plain"
    exit_code = 0
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, signal_handler)
    try:
        LOG.info("Starting homely-mqtt")
        uvicorn.run(
            "ibidem.homely_mqtt.main:app",
            host=settings.bind_address,
            port=settings.port,
            log_config=get_log_config(log_format, log_level),
            log_level=log_level,
            reload=settings.debug,
            access_log=settings.debug,
        )
    except ExitOnSignal:
        pass
    except Exception as e:
        LOG.exception(f"unwanted exception: {e}")
        exit_code = 113
    return exit_code


def signal_handler(signum, frame):
    raise ExitOnSignal()


@app.on_event("startup")
def _adjust_noisy_loggers():
    """These loggers become extremely noisy when on anything lower than WARNING"""
    for logger_name in NOISY_LOGGERS:
        logger = logging.getLogger(logger_name)
        if logger.getEffectiveLevel() < logging.WARNING:
            logger.setLevel(logging.WARNING)


@app.on_event("startup")
def launch_subsystems():
    LOG.info("Setting up subsystems")
    measurements_queue = Queue()
    manager.register_subsystem("homely", Homely(settings.homely, measurements_queue))
    manager.register_subsystem("mqtt", MqttManager(settings.mqtt, measurements_queue))
    manager.launch()


if __name__ == "__main__":
    sys.exit(main())
