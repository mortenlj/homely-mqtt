from collections import namedtuple
from uuid import uuid4, UUID

import pytest

from ibidem.homely_mqtt.models import Device

FloorData = namedtuple("FloorData", ["expected", "input"])


class TestDevice:
    @pytest.fixture(
        params=[
            FloorData("Basement", "Floor -1"),
            FloorData("Ground", "Floor 0"),
            FloorData("2", "Floor 1"),
        ]
    )
    def floor(self, request):
        return request.param

    @pytest.fixture(params=["Kitchen", "Living room", "Bedroom"])
    def room(self, request):
        return request.param

    @pytest.fixture(params=["Smoke Alarm", "Motion Sensor Mini", "Window Sensor"])
    def model_name(self, request):
        return request.param

    @pytest.fixture
    def device(self, floor, room, model_name):
        return Device(
            id=uuid4(),
            name="Test Device",
            location=f"{floor.input} - {room}",
            modelName=model_name,
        )

    def test_floor(self, device, floor):
        assert device.floor == floor.expected

    def test_room(self, device, room):
        assert device.room == room

    def test_model_name(self, device, model_name):
        assert device.model_name == model_name

    def test_validation(self):
        device_data = {
            "id": "b67efaab-1b5f-44a7-ae85-e54942499776",
            "name": "Bevegelse Stue",
            "serialNumber": "0015BC001A01A6CD",
            "location": "Floor 0 - Living room",
            "online": True,
            "modelId": "e806ca73-4be0-4bd2-98cb-71f273b09812",
            "modelName": "Motion Sensor Mini",
            "features": {
                "setup": {
                    "states": {
                        "appledenable": {
                            "value": True,
                            "lastUpdated": "2023-07-17T14:56:40.801Z",
                        },
                        "errledenable": {
                            "value": True,
                            "lastUpdated": "2023-07-17T14:56:40.770Z",
                        },
                    }
                },
                "alarm": {
                    "states": {
                        "alarm": {
                            "value": False,
                            "lastUpdated": "2023-12-13T21:34:05.808Z",
                        },
                        "tamper": {
                            "value": False,
                            "lastUpdated": "2022-11-17T12:01:45.308Z",
                        },
                        "sensitivitylevel": {"value": None, "lastUpdated": None},
                    }
                },
                "temperature": {
                    "states": {
                        "temperature": {
                            "value": 18.3,
                            "lastUpdated": "2023-12-14T10:59:16.956Z",
                        }
                    }
                },
                "battery": {
                    "states": {
                        "low": {
                            "value": False,
                            "lastUpdated": "2021-07-07T19:18:41.005Z",
                        },
                        "defect": {
                            "value": False,
                            "lastUpdated": "2021-07-07T19:18:41.014Z",
                        },
                        "voltage": {
                            "value": 2.7,
                            "lastUpdated": "2023-12-14T06:51:08.188Z",
                        },
                    }
                },
                "diagnostic": {
                    "states": {
                        "networklinkstrength": {
                            "value": 89,
                            "lastUpdated": "2023-12-14T10:29:48.421Z",
                        },
                        "networklinkaddress": {
                            "value": "0015BC002C1016B1",
                            "lastUpdated": "2023-11-17T17:02:08.307Z",
                        },
                    }
                },
            },
        }
        device = Device.model_validate(device_data)
        assert device.id == UUID("b67efaab-1b5f-44a7-ae85-e54942499776")
        assert device.name == "Bevegelse Stue"
        assert device.model_name == "Motion Sensor Mini"
        assert device.location == "Floor 0 - Living room"
