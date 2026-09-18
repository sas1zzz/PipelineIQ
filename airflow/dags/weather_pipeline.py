import os
from datetime import datetime, timezone

import pendulum
import psycopg
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from airflow.sdk import dag, task


DB_HOST = os.environ.get("PIPELINE_DB_HOST", "postgres")
DB_PORT = int(os.environ.get("PIPELINE_DB_PORT", "5432"))
DB_NAME = os.environ["PIPELINE_DB_NAME"]
DB_USER = os.environ["PIPELINE_DB_USER"]
DB_PASSWORD = os.environ["PIPELINE_DB_PASSWORD"]

PIPELINE_NAME = "weather_airflow_etl"


def get_database_connection():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def mark_pipeline_failed(context):
    """
    Runs automatically when the DAG fails.

    Finds the latest RUNNING pipeline record and marks it
    as FAILED with a useful error message.
    """

    finished_at = datetime.now(timezone.utc)

    dag_run = context.get("dag_run")

    if dag_run:
        run_id = dag_run.run_id
    else:
        run_id = "unknown"

    exception = context.get("exception")

    if exception:
        error_message = (
            f"Airflow DAG failed. "
            f"Run ID: {run_id}. "
            f"Error: {str(exception)}"
        )
    else:
        error_message = (
            f"Airflow DAG failed. "
            f"Run ID: {run_id}."
        )

    try:
        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE pipeline_runs
                    SET
                        status = %s,
                        finished_at = %s,
                        error_message = %s
                    WHERE id = (
                        SELECT id
                        FROM pipeline_runs
                        WHERE
                            pipeline_name = %s
                            AND status = 'RUNNING'
                        ORDER BY started_at DESC
                        LIMIT 1
                    )
                    """,
                    (
                        "FAILED",
                        finished_at,
                        error_message,
                        PIPELINE_NAME,
                    ),
                )

            connection.commit()

    except Exception as callback_error:
        print(
            "Could not update pipeline_runs after DAG failure: "
            f"{callback_error}"
        )


def get_weather_session():
    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=2,
        status_forcelist=[
            429,
            502,
            503,
            504,
        ],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy
    )

    session = requests.Session()

    session.mount(
        "https://",
        adapter,
    )

    session.mount(
        "http://",
        adapter,
    )

    return session


@dag(
    dag_id="pipelineiq_weather_pipeline",
    schedule="*/15 * * * *",
    start_date=pendulum.datetime(
        2026,
        9,
        18,
        tz="UTC",
    ),
    catchup=False,
    on_failure_callback=mark_pipeline_failed,
    tags=[
        "pipelineiq",
        "weather",
    ],
)
def pipelineiq_weather_pipeline():

    @task
    def start_pipeline():
        started_at = datetime.now(timezone.utc)

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO pipeline_runs
                    (
                        pipeline_name,
                        status,
                        started_at,
                        records_processed
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        PIPELINE_NAME,
                        "RUNNING",
                        started_at,
                        0,
                    ),
                )

                pipeline_run_id = cursor.fetchone()[0]

            connection.commit()

        print(
            f"Started pipeline run: {pipeline_run_id}"
        )

        return pipeline_run_id

    @task
    def extract():
        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        latitude,
                        longitude
                    FROM locations
                    ORDER BY id
                    """
                )

                locations = cursor.fetchall()

        weather_data = []

        session = get_weather_session()

        try:
            for (
                location_id,
                name,
                latitude,
                longitude,
            ) in locations:

                response = session.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "current": (
                            "temperature_2m,"
                            "relative_humidity_2m,"
                            "wind_speed_10m,"
                            "weather_code"
                        ),
                    },
                    timeout=15,
                )

                response.raise_for_status()

                current = response.json()["current"]

                weather_data.append(
                    {
                        "location_id": location_id,
                        "location_name": name,
                        "temperature": current[
                            "temperature_2m"
                        ],
                        "humidity": current[
                            "relative_humidity_2m"
                        ],
                        "wind_speed": current[
                            "wind_speed_10m"
                        ],
                        "weather_code": current[
                            "weather_code"
                        ],
                        "observed_at": current[
                            "time"
                        ],
                    }
                )

                print(
                    f"Extracted weather for {name}."
                )

        finally:
            session.close()

        print(
            f"Extracted weather for "
            f"{len(weather_data)} locations."
        )

        return weather_data

    @task
    def transform(weather_data):
        transformed_data = []

        for item in weather_data:

            temperature = float(
                item["temperature"]
            )

            humidity = float(
                item["humidity"]
            )

            wind_speed = float(
                item["wind_speed"]
            )

            if not 0 <= humidity <= 100:
                raise ValueError(
                    f"Invalid humidity for "
                    f"{item['location_name']}: "
                    f"{humidity}"
                )

            if wind_speed < 0:
                raise ValueError(
                    f"Invalid wind speed for "
                    f"{item['location_name']}: "
                    f"{wind_speed}"
                )

            weather_code = int(
                item["weather_code"]
            )

            if weather_code == 0:
                condition = "Clear"

            elif weather_code in (1, 2, 3):
                condition = "Cloudy"

            elif weather_code in (45, 48):
                condition = "Fog"

            elif 51 <= weather_code <= 67:
                condition = "Rain"

            elif 71 <= weather_code <= 77:
                condition = "Snow"

            elif 80 <= weather_code <= 82:
                condition = "Rain Showers"

            elif weather_code in (95, 96, 99):
                condition = "Thunderstorm"

            else:
                condition = "Unknown"

            transformed_data.append(
                {
                    "location_id": item[
                        "location_id"
                    ],
                    "temperature": temperature,
                    "humidity": humidity,
                    "wind_speed": wind_speed,
                    "weather_condition": condition,
                    "observed_at": item[
                        "observed_at"
                    ],
                }
            )

        print(
            f"Transformed "
            f"{len(transformed_data)} "
            f"weather records."
        )

        return transformed_data

    @task
    def load(weather_data):
        records_processed = 0

        with get_database_connection() as connection:
            with connection.cursor() as cursor:

                for item in weather_data:

                    observed_at = (
                        datetime.fromisoformat(
                            item["observed_at"]
                        )
                    )

                    if observed_at.tzinfo is None:
                        observed_at = (
                            observed_at.replace(
                                tzinfo=timezone.utc
                            )
                        )

                    cursor.execute(
                        """
                        INSERT INTO weather_observations
                        (
                            location_id,
                            temperature,
                            humidity,
                            wind_speed,
                            weather_condition,
                            observed_at,
                            created_at
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        """,
                        (
                            item["location_id"],
                            item["temperature"],
                            item["humidity"],
                            item["wind_speed"],
                            item[
                                "weather_condition"
                            ],
                            observed_at,
                            datetime.now(
                                timezone.utc
                            ),
                        ),
                    )

                    records_processed += 1

            connection.commit()

        print(
            f"Loaded {records_processed} "
            f"weather observations."
        )

        return records_processed

    @task
    def finish_pipeline(
        pipeline_run_id,
        records_processed,
    ):
        finished_at = datetime.now(
            timezone.utc
        )

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE pipeline_runs
                    SET
                        status = %s,
                        finished_at = %s,
                        records_processed = %s,
                        error_message = NULL
                    WHERE id = %s
                    """,
                    (
                        "SUCCESS",
                        finished_at,
                        records_processed,
                        pipeline_run_id,
                    ),
                )

            connection.commit()

        print(
            f"Pipeline run {pipeline_run_id} "
            f"completed successfully."
        )

    pipeline_run_id = start_pipeline()

    weather_data = extract()

    transformed_data = transform(
        weather_data
    )

    records_processed = load(
        transformed_data
    )

    finish_pipeline(
        pipeline_run_id,
        records_processed,
    )


pipelineiq_weather_pipeline()