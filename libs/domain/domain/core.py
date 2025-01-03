from datetime import datetime
from enum import Enum
from time import time
from typing import Any, Self

from pydantic import BaseModel


class Schema(BaseModel):
    """
    Base class for all schemas.
    It is a wrapper around pydantic.BaseModel, adding some utility methods.
    """

    def unpack(self):
        """Unpack the schema into a dictionary."""
        return self.model_dump()

    @classmethod
    def field_names(cls):
        """Get the field names of the schema."""
        return cls.model_fields.keys()

    @classmethod
    def serialize(cls, schema: Self):
        """Unpack the schema into a dictionary."""
        return schema.model_dump()

    @classmethod
    def parse(cls, obj: Any) -> Self:
        """Validate the obj."""
        return cls.model_validate(obj)


def now_timestamp() -> int:
    """Get the current timestamp in milliseconds."""
    return int(time() * 1000)


def iso_to_timestamp(iso_datetime: str) -> int:
    """Convert an ISO 8601 datetime string to a timestamp in milliseconds."""
    return int(datetime.fromisoformat(iso_datetime).timestamp() * 1000)


class DeploymentEnv(str, Enum):
    """Deployment environment names"""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
