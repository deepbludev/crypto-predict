from pydantic import BaseModel


class Schema(BaseModel):
    def unpack(self):
        return self.model_dump()

    @classmethod
    def field_names(cls):
        return cls.model_fields.keys()
