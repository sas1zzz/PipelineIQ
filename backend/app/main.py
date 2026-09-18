from fastapi import FastAPI
from sqlalchemy import select, text

from backend.app.auth import router as auth_router
from backend.app.database import SessionLocal, engine
from backend.app.models import Location
from backend.app.pipeline_runs import router as pipeline_runs_router
from backend.app.schemas import LocationCreate, LocationResponse
from backend.app.weather import router as weather_router


app = FastAPI(
    title="PipelineIQ API",
    description="Backend API for the PipelineIQ data pipeline dashboard",
    version="0.1.0",
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {"status": "ok"}


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

@app.get("/health/database")
def database_health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "test_query_result": value,
    }


# ============================================================
# LOCATION APIs
# ============================================================

@app.get(
    "/api/locations",
    response_model=list[LocationResponse],
)
def get_locations():
    with SessionLocal() as session:
        result = session.execute(
            select(Location).order_by(Location.name)
        )

        locations = result.scalars().all()

    return locations


@app.post(
    "/api/locations",
    response_model=LocationResponse,
    status_code=201,
)
def create_location(location_data: LocationCreate):
    with SessionLocal() as session:
        location = Location(
            name=location_data.name,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
        )

        session.add(location)
        session.commit()
        session.refresh(location)

        return location


# ============================================================
# WEATHER APIs
# ============================================================

app.include_router(weather_router)


# ============================================================
# PIPELINE RUN APIs
# ============================================================

app.include_router(pipeline_runs_router)


# ============================================================
# AUTHENTICATION APIs
# ============================================================

app.include_router(auth_router)