from pydantic import BaseModel, validator
class BaseNormalizer:
    @classmethod
    def normalize(cls, data, vendor: str):
        raise NotImplementedError("Implement in subclass")
    @classmethod
    def validate(cls, data):
        raise NotImplementedError("Use Pydantic")