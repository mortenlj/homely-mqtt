import datetime
import logging
from queue import Queue
from uuid import UUID

import requests
import socketio
from pydantic import BaseModel

from ibidem.homely_mqtt.models import Device, Measurement
from ibidem.homely_mqtt.subsystems import SubsystemState

AUTH_URL = "https://sdk.iotiliti.cloud/homely/oauth/token"
REFRESH_URL = "https://sdk.iotiliti.cloud/homely/oauth/refresh-token"
LOCATIONS_URL = "https://sdk.iotiliti.cloud/homely/locations"
HOME_URL = "https://sdk.iotiliti.cloud/homely/home"
SOCKET_URL = "https://sdk.iotiliti.cloud/"

LOG = logging.getLogger(__name__)


class HomelyAuth(requests.auth.AuthBase):
    def __init__(self, token=None):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


class Event(BaseModel):
    """{
        'type': 'device-state-changed',
        'data': {
            'deviceId': 'ba265ebe-1aa1-4361-a5e1-e93bcd2fd9af',
            'gatewayId': 'a9eea2d8-9ea9-45f8-a7de-597df33fe6a3',
            'locationId': 'a6f93ada-d626-477e-9aee-fc12a0a01c61',
            'modelId': 'ffe30099-92c5-4471-879f-41f412d423ab',
            'rootLocationId': 'b4dbbfd9-dd8d-4db6-a5eb-7ce7a2d2397f',
            'changes': [
                {
                    'feature': 'diagnostic',
                    'stateName': 'networklinkstrength',
                    'value': 47,
                    'lastUpdated': '2023-12-02T14:02:02.391Z'
                }
            ],
            'partnerCode': 1275
        }
    }"""

    type: str
    device_id: UUID
    changes: list[Measurement]

    @classmethod
    def parse(cls, data):
        return cls(
            type=data["type"],
            device_id=UUID(data["data"]["deviceId"]),
            changes=[Measurement.model_validate(change) for change in data["data"]["changes"]],
        )


class Homely:
    def __init__(self, settings, measurement_queue: Queue):
        self.measurement_queue = measurement_queue
        self._username = settings.username
        self._password = settings.password
        self._location_name = settings.location
        self._session = requests.Session()
        self._locations = []
        self._state = None
        self._home = None

    def __call__(self, state: SubsystemState):
        self._state = state
        self._authenticate()
        sio = socketio.Client()
        sio.on("event", self._on_event)
        self._update_locations()
        self._update_devices()
        url = SOCKET_URL + f"?locationId={self._home['locationId']}&token={self._access_token}"
        sio.connect(url, headers={"Authorization": f"Bearer {self._access_token}"})
        self._state.ready = True
        while True:
            try:
                sio.wait()
                if datetime.datetime.now() > self._refresh_after:
                    self._refresh()
                    self._state.ready = True
                    self._update_devices()
            except requests.RequestException as e:
                if not e.response or 400 <= e.response.status_code < 500:
                    self._state.ready = False

    def _on_event(self, data):
        event = Event.parse(data)
        LOG.debug("event received: %r", event)
        if event.type != "device-state-changed":
            LOG.warning(f"Unknown event type {event.type}")
            return
        device = self._devices[event.device_id]
        for measurement in event.changes:
            measurement.device = device
            LOG.info(f"Captured measurement: {measurement.device.slug}/{measurement.sensor_name}: {measurement.value}")
            self.measurement_queue.put(measurement)

    def _update_locations(self):
        resp = self._session.get(LOCATIONS_URL)
        resp.raise_for_status()
        self._locations = resp.json()
        LOG.info(f"Got locations: {self._locations}")
        for location in self._locations:
            if location["name"] == self._location_name:
                LOG.info(f"Using location {location}")
                self._home = location

    def _update_devices(self):
        resp = self._session.get(f"{HOME_URL}/{self._home['locationId']}")
        resp.raise_for_status()
        devices = {}
        for device_data in resp.json()["devices"]:
            device = Device.model_validate(device_data)
            devices[device.id] = device
            self._update_measurements(device_data, device)
        self._devices = devices
        LOG.info(f"Got devices: {self._devices}")

    def _authenticate(self):
        resp = self._session.post(
            AUTH_URL,
            {
                "username": self._username,
                "password": self._password,
            },
        )
        resp.raise_for_status()
        LOG.info("Successfully authenticated with Homely API")
        auth_data = resp.json()
        self._update_auth_data(auth_data)

    def _refresh(self):
        resp = self._session.post(REFRESH_URL, {"refresh_token": self._refresh_token})
        resp.raise_for_status()
        LOG.error("Successfully refreshed access token with Homely API")
        auth_data = resp.json()
        self._update_auth_data(auth_data)

    def _update_auth_data(self, auth_data):
        self._session.auth = HomelyAuth(auth_data["access_token"])
        self._access_token = auth_data["access_token"]
        self._refresh_token = auth_data["refresh_token"]
        self._refresh_after = datetime.datetime.now() + datetime.timedelta(seconds=auth_data["expires_in"])
        LOG.debug(f"Access token expires at {self._refresh_after}")

    def _update_measurements(self, device_data, device):
        for feature_name, feature_data in device_data["features"].items():
            if feature_name == "setup":
                continue
            for state_name, state_data in feature_data["states"].items():
                state_value = state_data["value"]
                if state_value is None:
                    continue
                if isinstance(state_value, str):
                    continue
                value = float(state_value) if isinstance(state_value, bool) else state_value
                measurement = Measurement(
                    device=device,
                    feature=feature_name,
                    stateName=state_name,
                    value=value
                )
                LOG.info(f"Fetched measurement: {measurement.device.slug}/{measurement.sensor_name}: {measurement.value}")
                self.measurement_queue.put(measurement)
