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
