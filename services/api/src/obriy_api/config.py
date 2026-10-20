from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    fake_home_lat: Annotated[float, Field(ge=-90, le=90)] = 50.45
    fake_home_lon: Annotated[float, Field(ge=-180, le=180)] = 30.52
