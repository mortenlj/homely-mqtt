from collections import namedtuple
from uuid import uuid4

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
        return Device(id=uuid4(), name="Test Device", location=f"{floor.input} - {room}", modelName=model_name)

    def test_floor(self, device, floor):
        assert device.floor == floor.expected

    def test_room(self, device, room):
        assert device.room == room

    def test_model_name(self, device, model_name):
        assert device.modelName == model_name
