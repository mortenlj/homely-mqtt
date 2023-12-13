from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field
from slugify import slugify


class Device(BaseModel):
    id: UUID
    name: str
    model_name: str = Field(alias="modelName")
    location: str

    @property
    def floor(self):
        split_idx = self.location.rfind("-")
        if split_idx > 0:
            floor = self.location[:split_idx].strip()
            floor_number = int(floor.split()[-1])
            if floor_number == 0:
                return "Ground"
            if floor_number < 0:
                return "Basement"
            return str(floor_number + 1)
        return self.location

    @property
    def room(self):
        split_idx = self.location.rfind("-")
        if split_idx > 0:
            return self.location[split_idx + 1 :].strip()
        return self.location

    @property
    def slug(self):
        return slugify(f"{self.name} {self.floor} {self.room}", separator="_")


class Measurement(BaseModel):
    device: Optional[Device] = None
    feature: str
    state_name: str = Field(alias="stateName")
    value: Union[float, int, str]

    @property
    def sensor_name(self):
        if self.feature == self.state_name:
            return self.feature
        if self.feature == "diagnostic":
            return self.state_name
        return f"{self.feature}_{self.state_name}"
