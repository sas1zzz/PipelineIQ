const DISPLAY_TIMEZONE = "Asia/Kolkata";


async function fetchJson(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(
            `${response.status} ${response.statusText}`
        );
    }

    return response.json();
}


function formatDate(value) {
    if (!value) {
        return "-";
    }

    return new Date(value).toLocaleString("en-IN", {
        timeZone: DISPLAY_TIMEZONE,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true
    });
}


function formatTime(value) {
    return new Date(value).toLocaleTimeString("en-IN", {
        timeZone: DISPLAY_TIMEZONE,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true
    });
}


function statusClass(status) {
    if (status === "SUCCESS") {
        return "status-success";
    }

    if (status === "FAILED") {
        return "status-failed";
    }

    return "";
}


async function loadDashboard() {
    const errorBox = document.getElementById("errorBox");

    errorBox.classList.add("hidden");

    try {
        const [
            locations,
            weather,
            pipelineRuns
        ] = await Promise.all([
            fetchJson("/api/locations"),
            fetchJson("/api/weather"),
            fetchJson("/api/pipeline-runs")
        ]);


        // ----------------------------------------------------
        // SUMMARY CARDS
        // ----------------------------------------------------

        document.getElementById("locationCount").textContent =
            locations.length;

        document.getElementById("weatherCount").textContent =
            weather.length;


        const airflowRuns = pipelineRuns.filter(
            run => run.pipeline_name === "weather_airflow_etl"
        );

        const latestRun = airflowRuns.length > 0
            ? airflowRuns[0]
            : null;


        if (latestRun) {
            document.getElementById("pipelineStatus").textContent =
                latestRun.status;

            document.getElementById("recordsProcessed").textContent =
                latestRun.records_processed;
        } else {
            document.getElementById("pipelineStatus").textContent =
                "No runs";

            document.getElementById("recordsProcessed").textContent =
                "0";
        }


        // ----------------------------------------------------
        // WEATHER
        // ----------------------------------------------------

        renderWeather(
            weather,
            locations
        );


        // ----------------------------------------------------
        // PIPELINE HISTORY
        // ----------------------------------------------------

        renderPipelineRuns(
            airflowRuns
        );


        // ----------------------------------------------------
        // LAST UPDATED
        // ----------------------------------------------------

        document.getElementById("weatherUpdated").textContent =
            `Updated ${formatTime(new Date())} IST`;

    } catch (error) {
        console.error(error);

        errorBox.textContent =
            `Dashboard error: ${error.message}`;

        errorBox.classList.remove("hidden");
    }
}


function renderWeather(
    weather,
    locations
) {
    const container =
        document.getElementById("weatherTable");


    if (!weather.length) {
        container.innerHTML =
            "<p>No weather records found.</p>";

        return;
    }


    const locationMap = {};

    for (const location of locations) {
        locationMap[location.id] =
            location.name;
    }


    const latestByLocation = {};

    for (const item of weather) {

        const existing =
            latestByLocation[item.location_id];

        if (
            !existing ||
            new Date(item.observed_at) >
            new Date(existing.observed_at)
        ) {
            latestByLocation[item.location_id] =
                item;
        }
    }


    const rows =
        Object.values(latestByLocation)
            .map(item => {

                const temperature =
                    Number(item.temperature);

                const humidity =
                    Number(item.humidity);

                const windSpeed =
                    Number(item.wind_speed);

                return `
                    <tr>
                        <td>
                            ${locationMap[item.location_id] || "Unknown"}
                        </td>

                        <td>
                            ${temperature.toFixed(1)} °C
                        </td>

                        <td>
                            ${humidity.toFixed(0)}%
                        </td>

                        <td>
                            ${windSpeed.toFixed(1)}
                        </td>

                        <td>
                            ${item.weather_condition}
                        </td>

                        <td>
                            ${formatDate(item.observed_at)}
                        </td>
                    </tr>
                `;
            })
            .join("");


    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Location</th>
                    <th>Temperature</th>
                    <th>Humidity</th>
                    <th>Wind Speed</th>
                    <th>Condition</th>
                    <th>Observed (IST)</th>
                </tr>
            </thead>

            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}


function renderPipelineRuns(runs) {
    const container =
        document.getElementById("pipelineTable");


    if (!runs.length) {
        container.innerHTML =
            "<p>No Airflow pipeline runs found.</p>";

        return;
    }


    const rows =
        runs
            .slice(0, 10)
            .map(run => {

                return `
                    <tr>
                        <td>
                            ${run.pipeline_name}
                        </td>

                        <td class="${statusClass(run.status)}">
                            ${run.status}
                        </td>

                        <td>
                            ${run.records_processed}
                        </td>

                        <td>
                            ${formatDate(run.started_at)}
                        </td>

                        <td>
                            ${formatDate(run.finished_at)}
                        </td>
                    </tr>
                `;
            })
            .join("");


    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Pipeline</th>
                    <th>Status</th>
                    <th>Records</th>
                    <th>Started (IST)</th>
                    <th>Finished (IST)</th>
                </tr>
            </thead>

            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}


// ------------------------------------------------------------
// REFRESH BUTTON
// ------------------------------------------------------------

document
    .getElementById("refreshBtn")
    .addEventListener(
        "click",
        loadDashboard
    );


// ------------------------------------------------------------
// INITIAL LOAD
// ------------------------------------------------------------

loadDashboard();


// ------------------------------------------------------------
// AUTO REFRESH
// ------------------------------------------------------------

setInterval(
    loadDashboard,
    60000
);