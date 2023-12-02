import datetime
import logging
from uuid import UUID

import requests
import socketio
from pydantic import BaseModel

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


class Device(BaseModel):
    id: UUID
    name: str
    location: str


class Homely:
    def __init__(self, username, password, location_name):
        self._state = None
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._locations = []
        self._location_name = location_name
        self._home = None

    def __call__(self, state: SubsystemState):
        self._state = state
        self._authenticate()
        sio = socketio.Client()
        sio.on("*", self._on_event)
        self._update_locations()
        self._update_devices()
        url = SOCKET_URL + f"?locationId={self._home['locationId']}&token={self._access_token}"
        sio.connect(url, headers={
            "Authorization": f"Bearer {self._access_token}"
        })
        while True:
            try:
                sio.wait()
                if datetime.datetime.now() > self._refresh_after:
                    self._refresh()
                self._state.ready = True
            except requests.RequestException as e:
                if not e.response or 400 <= e.response.status_code < 500:
                    self._state.ready = False

    def _on_event(self, data):
        LOG.debug('event received:', data)

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
        self._devices = devices
        LOG.info(f"Got devices: {self._devices}")

    def _authenticate(self):
        resp = self._session.post(AUTH_URL, {
            "username": self._username,
            "password": self._password,
        })
        resp.raise_for_status()
        LOG.info("Successfully authenticated with Homely API")
        auth_data = resp.json()
        self._update_auth_data(auth_data)

    def _refresh(self):
        resp = self._session.post(REFRESH_URL, {
            "refresh_token": self._refresh_token
        })
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
