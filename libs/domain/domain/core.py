from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel

type NDFloats = NDArray[np.floating[Any]]
"""Type alias for a numpy array of floats."""


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
