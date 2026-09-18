from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================
# LOCATION SCHEMAS
# ============================================================

class LocationCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100
    )

    latitude: float = Field(
        ge=-90,
        le=90
    )

    longitude: float = Field(
        ge=-180,
        le=180
    )


class LocationResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# ============================================================
# WEATHER OBSERVATION SCHEMAS
# ============================================================

class WeatherObservationCreate(BaseModel):
    location_id: int = Field(
        gt=0
    )

    temperature: float

    humidity: float = Field(
        ge=0,
        le=100
    )

    wind_speed: float = Field(
        ge=0
    )

    weather_condition: str = Field(
        min_length=1,
        max_length=100
    )

    observed_at: datetime


class WeatherObservationResponse(BaseModel):
    id: int
    location_id: int
    temperature: float
    humidity: float
    wind_speed: float
    weather_condition: str
    observed_at: datetime
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# ============================================================
# PIPELINE RUN SCHEMAS
# ============================================================

class PipelineRunCreate(BaseModel):
    pipeline_name: str = Field(
        min_length=1,
        max_length=100
    )

    status: str = Field(
        min_length=1,
        max_length=20
    )

    started_at: datetime

    finished_at: datetime | None = None

    records_processed: int = Field(
        default=0,
        ge=0
    )

    error_message: str | None = None


class PipelineRunResponse(BaseModel):
    id: int
    pipeline_name: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    records_processed: int
    error_message: str | None

    model_config = {
        "from_attributes": True
    }