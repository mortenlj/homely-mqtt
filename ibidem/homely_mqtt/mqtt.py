import logging
import socket
import time
import uuid

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes

from ibidem.homely_mqtt.models import Measurement
from ibidem.homely_mqtt.subsystems import SubsystemState

PUBLISH_TIMEOUT_SECONDS = 5 * 60  # 5 minutes
KEEPALIVE_SECONDS = 6 * 60  # 6 minutes

LOG = logging.getLogger(__name__)


def make_client_id():
    return f"homely-mqtt-{socket.gethostname()}-{uuid.uuid4()}"


class MqttException(Exception):
    def __str__(self):
        return f"{self.__class__.__name__}: {self.args[0] % self.args[1:]}"


class MqttManager:
    def __init__(self, settings, measurement_queue):
        self.measurement_queue = measurement_queue
        self._state = None
        self._client = mqtt.Client(client_id=make_client_id(), protocol=mqtt.MQTTv5)
        if settings.ca_certs:
            self._client.tls_set(settings.ca_certs, settings.certfile, settings.keyfile)
        self._client.enable_logger()
        self._client.loop_start()
        self._client.connect(settings.broker_url, settings.broker_port, keepalive=KEEPALIVE_SECONDS)
        self._topic_prefix = settings.topic_prefix

    def __call__(self, state: SubsystemState):
        self._state = state
        self._state.ready = True
        while True:
            try:
                measurement = self.measurement_queue.get()
                self.send(measurement)
            except Exception as e:
                LOG.exception(e)

    def send(self, measurement: Measurement):
        properties = mqtt.Properties(PacketTypes.PUBLISH)
        properties.UserProperty = [
            ("floor", measurement.device.floor),
            ("room", measurement.device.room),
        ]
        topic = f"{self._topic_prefix}/{measurement.device.slug}/sensor/{measurement.sensor_name}"
        value = measurement.value
        mmi = self._client.publish(topic, value, qos=1, properties=properties)
        if mmi.rc == mqtt.MQTT_ERR_NO_CONN:
            LOG.warning("Broker not connected, waiting for message to be published")
            self.mmi_wait_for_publish(mmi)
        elif mmi.rc == mqtt.MQTT_ERR_QUEUE_SIZE:
            raise MqttException("MQTT output queue full")
        LOG.debug("Published measurement on topic %s: %r", topic, value)
        return mmi

    @staticmethod
    def mmi_wait_for_publish(mmi, timeout=PUBLISH_TIMEOUT_SECONDS):
        start = time.time()
        while time.time() < (start + timeout):
            if mmi.rc == mqtt.MQTT_ERR_SUCCESS:
                return
            try:
                mmi.wait_for_publish(timeout=timeout/10)
            except RuntimeError as e:
                LOG.warning(e)
        raise MqttException("Failed to publish message after timeout: %s", mqtt.error_string(mmi.rc))
