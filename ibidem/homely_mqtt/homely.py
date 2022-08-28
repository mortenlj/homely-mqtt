import logging
import time

import requests

from ibidem.homely_mqtt.subsystems import SubsystemState

AUTH_URL = "https://sdk.iotiliti.cloud/homely/oauth/token"
REFRESH_URL = "https://sdk.iotiliti.cloud/homely/oauth/refresh-token"
LOCATIONS_URL = "https://sdk.iotiliti.cloud/homely/locations"
HOME_URL = "https://sdk.iotiliti.cloud/homely/home"
SOCKET_URL = "https://sdk.iotiliti.cloud/"

LOG = logging.getLogger(__name__)


class Homely:
    def __init__(self, username, password):
        self._state = None
        self._username = username
        self._password = password
        self._session = requests.Session()

    def __call__(self, state: SubsystemState):
        self._state = state
        auth_data = self._authenticate()
        while True:
            LOG.debug(auth_data)
            time.sleep(auth_data["expires_in"])
            try:
                auth_data = self._refresh(auth_data)
                self._state.ready = True
            except requests.RequestException as e:
                if not e.response or 400 <= e.response.status_code < 500:
                    self._state.ready = False

    def _authenticate(self):
        resp = self._session.post(AUTH_URL, {
            "username": self._username,
            "password": self._password,
        })
        resp.raise_for_status()
        LOG.warning("Successfully authenticated with Homely API")
        return resp.json()

    def _refresh(self, auth_data):
        resp = self._session.post(REFRESH_URL, {
            "refresh_token": auth_data["refresh_token"]
        })
        resp.raise_for_status()
        LOG.error("Successfully refreshed access token with Homely API")
        return resp.json()
