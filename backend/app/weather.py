from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import WeatherObservation, Location
from .schemas import (
    WeatherObservationCreate,
    WeatherObservationResponse,
)


router = APIRouter(
    prefix="/api/weather",
    tags=["Weather"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "",
    response_model=WeatherObservationResponse,
    status_code=201,
)
def create_weather(
    weather: WeatherObservationCreate,
    db: Session = Depends(get_db),
):
    location = (
        db.query(Location)
        .filter(Location.id == weather.location_id)
        .first()
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    observation = WeatherObservation(
        location_id=weather.location_id,
        temperature=weather.temperature,
        humidity=weather.humidity,
        wind_speed=weather.wind_speed,
        weather_condition=weather.weather_condition,
        observed_at=weather.observed_at,
    )

    db.add(observation)
    db.commit()
    db.refresh(observation)

    return observation


@router.get(
    "",
    response_model=list[WeatherObservationResponse],
)
def get_weather(
    db: Session = Depends(get_db),
):
    observations = (
        db.query(WeatherObservation)
        .order_by(
            WeatherObservation.observed_at.desc()
        )
        .all()
    )

    return observations


@router.get(
    "/{weather_id}",
    response_model=WeatherObservationResponse,
)
def get_weather_by_id(
    weather_id: int,
    db: Session = Depends(get_db),
):
    observation = (
        db.query(WeatherObservation)
        .filter(
            WeatherObservation.id == weather_id
        )
        .first()
    )

    if not observation:
        raise HTTPException(
            status_code=404,
            detail="Weather observation not found",
        )

    return observation