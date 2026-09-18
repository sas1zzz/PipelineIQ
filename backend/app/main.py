from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from sqlalchemy import select, text

from fastapi.staticfiles import StaticFiles

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
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"


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
# API ROUTERS
# ============================================================

app.include_router(weather_router)

app.include_router(pipeline_runs_router)

app.include_router(auth_router)


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )