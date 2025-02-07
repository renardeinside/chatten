from pathlib import PosixPath
from pydantic import BaseModel


class Volume(BaseModel):
    catalog: str
    schema: str 
    name: str

    @property
    def as_path(self) -> PosixPath:
        return PosixPath(f"{self.catalog}/{self.schema}/{self.name}")


class Config(BaseModel):
    serving_endpoint_name: str
    volume: Volume
