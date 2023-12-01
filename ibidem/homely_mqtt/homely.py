import datetime
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


class HomelyAuth(requests.auth.AuthBase):
    def __init__(self, token=None):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


class Homely:
    def __init__(self, username, password):
        self._state = None
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._locations = []

    def __call__(self, state: SubsystemState):
        self._state = state
        self._authenticate()
        while True:
            time.sleep(5)
            try:
                if datetime.datetime.now() > self._refresh_after:
                    self._refresh()
                    self._locations = self._get_locations()
                    LOG.info(f"Got locations: {self._locations}")
                self._state.ready = True
            except requests.RequestException as e:
                if not e.response or 400 <= e.response.status_code < 500:
                    self._state.ready = False

    def _get_locations(self):
        resp = self._session.get(LOCATIONS_URL)
        resp.raise_for_status()
        return resp.json()

    def _authenticate(self):
        resp = self._session.post(AUTH_URL, {
            "username": self._username,
            "password": self._password,
        })
        resp.raise_for_status()
        LOG.info("Successfully authenticated with Homely API")
        auth_data = resp.json()
        self._update_auth(auth_data)

    def _update_auth(self, auth_data):
        self._session.auth = HomelyAuth(auth_data["access_token"])
        self._refresh_token = auth_data["refresh_token"]
        self._refresh_after = datetime.datetime.now() + datetime.timedelta(seconds=auth_data["expires_in"])
        LOG.debug(f"Access token expires at {self._refresh_after}")
        LOG.debug("Access token: %s", auth_data["access_token"])

    def _refresh(self):
        resp = self._session.post(REFRESH_URL, {
            "refresh_token": self._refresh_token
        })
        resp.raise_for_status()
        LOG.error("Successfully refreshed access token with Homely API")
        auth_data = resp.json()
        self._update_auth(auth_data)
