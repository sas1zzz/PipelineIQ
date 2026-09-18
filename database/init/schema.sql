CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_latitude
        CHECK (latitude >= -90 AND latitude <= 90),

    CONSTRAINT valid_longitude
        CHECK (longitude >= -180 AND longitude <= 180)
);

CREATE TABLE IF NOT EXISTS weather_observations (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    humidity DOUBLE PRECISION NOT NULL,
    wind_speed DOUBLE PRECISION NOT NULL,
    weather_condition VARCHAR(100) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_weather_location
        FOREIGN KEY (location_id)
        REFERENCES locations(id)
        ON DELETE CASCADE,

    CONSTRAINT valid_humidity
        CHECK (humidity >= 0 AND humidity <= 100),

    CONSTRAINT valid_wind_speed
        CHECK (wind_speed >= 0)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    records_processed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,

    CONSTRAINT valid_pipeline_status
        CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),

    CONSTRAINT valid_records_processed
        CHECK (records_processed >= 0)
);

CREATE INDEX IF NOT EXISTS idx_weather_location_time
    ON weather_observations (location_id, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at
    ON pipeline_runs (started_at DESC);

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);