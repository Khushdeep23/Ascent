// =====================================
// ASCENT LIVE TELEMETRY
// =====================================


// =====================================
// DOM ELEMENTS
// =====================================

const timer =
    document.getElementById("missionTimer");

const thrustElement =
    document.getElementById("thrustValue");

const pressureElement =
    document.getElementById("pressureValue");

const temperatureElement =
    document.getElementById("temperatureValue");

const rpmElement =
    document.getElementById("rpmValue");

const fuelFlowElement =
    document.getElementById("fuelFlowValue");

const healthElement =
    document.getElementById("healthValue");

const statusElement =
    document.getElementById("statusText");

const aiMessageElement =
    document.getElementById("aiMessage");

const riskElement =
    document.getElementById("riskLevel");

const confidenceElement =
    document.getElementById("confidenceValue");

const recommendationElement =
    document.getElementById("recommendationValue");

const decisionElement =
    document.getElementById("aiDecision");

const actionElement =
    document.getElementById("aiAction");

// ML Anomaly card elements

const mlAnomalyMessageElement =
    document.getElementById("mlAnomalyMessage");

const mlAnomalyScoreElement =
    document.getElementById("mlAnomalyScore");

const mlAnomalyStatusElement =
    document.getElementById("mlAnomalyStatus");


// =====================================
// REASONING TRAIL STEPPER
// =====================================
// Animates OBSERVE -> DIAGNOSE -> RISK -> DECIDE -> ACT -> VERIFY
// on every telemetry poll, then rests on whichever stage best
// represents the current situation: VERIFY when risk is LOW
// (loop is idle / confirming nominal), ACT when risk is
// MEDIUM/HIGH (AI is actively intervening).

const STAGES = ["observe", "diagnose", "risk", "decide", "act", "verify"];

let stageAnimationTimeout = null;


function animateReasoningTrail(restingStage) {

    if (stageAnimationTimeout) {

        clearTimeout(stageAnimationTimeout);

    }


    const restIndex =
        STAGES.indexOf(restingStage);

    let i = 0;


    function paintUpTo(index) {

        STAGES.forEach((stage, idx) => {

            const el =
                document.querySelector(
                    '.trail-stage[data-stage="' + stage + '"]'
                );

            if (!el) return;

            el.classList.remove(
                "stage-active",
                "stage-complete"
            );

            if (idx < index) {

                el.classList.add(
                    "stage-complete"
                );

            }

            if (idx === index) {

                el.classList.add(
                    "stage-active"
                );

            }

        });

    }


    function tick() {

        paintUpTo(i);

        if (i < restIndex) {

            i++;

            stageAnimationTimeout =
                setTimeout(tick, 90);

        }

    }


    tick();

}


// =====================================
// STABILIZING BANNER
// =====================================
// Fires once, right on the poll where risk_level transitions
// from MEDIUM/HIGH down to LOW — i.e. the exact moment a fault
// has just cleared. Tracks the previously-seen risk level so it
// can detect that transition; only shows the banner on that one
// poll, since the next poll's "previous" value is already LOW
// and won't re-trigger it.

let previousRiskLevel = null;

let stabilizingBannerTimeout = null;


function maybeShowStabilizingBanner(currentRiskLevel) {

    const banner =
        document.getElementById("stabilizingBanner");

    const justCleared =
        (previousRiskLevel === "MEDIUM" || previousRiskLevel === "HIGH")
        &&
        currentRiskLevel === "LOW";


    if (justCleared && banner) {

        if (stabilizingBannerTimeout) {

            clearTimeout(stabilizingBannerTimeout);

        }

        banner.classList.add("visible");

        stabilizingBannerTimeout =
            setTimeout(() => {

                banner.classList.remove("visible");

            }, 4000);

    }


    previousRiskLevel = currentRiskLevel;

}


// =====================================
// PRESSURE CHART
// =====================================

const ctx =
    document.getElementById("pressureChart");


const labels = [];

const pressureData = [];


for (let i = 0; i < 20; i++) {

    labels.push("");

    pressureData.push(95);

}


const pressureChart = new Chart(
    ctx,
    {

        type: "line",

        data: {

            labels: labels,

            datasets: [

                {

                    label:
                        "Chamber Pressure",

                    data:
                        pressureData,

                    borderColor:
                        "#45C8FF",

                    borderWidth:
                        3,

                    fill:
                        false,

                    tension:
                        0.35,

                    pointRadius:
                        0

                }

            ]

        },

        options: {

            responsive:
                true,

            animation:
                false,

            plugins: {

                legend: {

                    labels: {

                        color:
                            "white"

                    }

                }

            },

            scales: {

                x: {

                    ticks: {

                        color:
                            "#8FA4C9"

                    },

                    grid: {

                        color:
                            "rgba(255,255,255,.04)"

                    }

                },

                y: {

                    ticks: {

                        color:
                            "#8FA4C9"

                    },

                    grid: {

                        color:
                            "rgba(255,255,255,.04)"

                    }

                }

            }

        }

    }
);


// =====================================
// UPDATE DASHBOARD
// =====================================

async function updateDashboard() {

    try {

        const response =
            await fetch("/telemetry");


        if (!response.ok) {

            throw new Error(
                "Telemetry API error"
            );

        }


        const telemetry =
            await response.json();


        const engine =
            telemetry.engine;

        const ai =
            telemetry.ai;

        const mlAnomaly =
            telemetry.ml_anomaly;


        // =================================
        // MISSION TIMER
        // =================================

        timer.textContent =
            "T + " +
            telemetry.mission.mission_time +
            " s";


        // =================================
        // ENGINE TELEMETRY
        // =================================

        thrustElement.textContent =
            Number(
                engine.thrust_kN
            ).toFixed(1)
            + " kN";


        pressureElement.textContent =
            Number(
                engine.chamber_pressure_bar
            ).toFixed(2)
            + " bar";


        temperatureElement.textContent =
            engine.temperature_K
            + " K";


        rpmElement.textContent =
            engine.rpm;


        fuelFlowElement.textContent =
            Number(
                engine.fuel_flow_kg_s
            ).toFixed(1)
            + " kg/s";


        healthElement.textContent =
            Number(
                engine.health
            ).toFixed(1)
            + "%";


        // =================================
        // VALUE ALERT HIGHLIGHT
        // =================================
        // Purely visual — highlights the telemetry numbers
        // themselves when the AI's risk_level is elevated, so a
        // fault is visible on the raw values, not just in the AI
        // panel. Reuses existing .warning/.danger color classes
        // and adds a pulse via .pulse-alert. Cleared automatically
        // once risk_level returns to LOW.

        const valueAlertClass =
            ai.risk_level === "HIGH"
                ? "danger pulse-alert"
                : ai.risk_level === "MEDIUM"
                ? "warning pulse-alert"
                : "";

        [
            thrustElement,
            pressureElement,
            temperatureElement,
            rpmElement,
            fuelFlowElement,
            healthElement
        ].forEach(el => {

            if (el) {

                el.className = valueAlertClass;

            }

        });


        // =================================
        // ENGINE STATUS
        // =================================

        statusElement.innerHTML =
            '<span class="live-dot"></span>'
            +
            engine.status;


        statusElement.className =
            "";


        if (
            ai.risk_level === "LOW"
        ) {

            statusElement.classList.add(
                "nominal-status"
            );

        }

        else if (
            ai.risk_level === "MEDIUM"
        ) {

            statusElement.classList.add(
                "warning-status"
            );

        }

        else {

            statusElement.classList.add(
                "danger-status"
            );

        }


        // =================================
        // AI DIAGNOSIS
        // =================================

        aiMessageElement.textContent =
            ai.diagnosis;


        // =================================
        // AI RISK
        // =================================

        riskElement.textContent =
            ai.risk_level;


        riskElement.className =
            "";


        if (
            ai.risk_level === "LOW"
        ) {

            riskElement.classList.add(
                "safe"
            );

        }

        else if (
            ai.risk_level === "MEDIUM"
        ) {

            riskElement.classList.add(
                "warning"
            );

        }

        else {

            riskElement.classList.add(
                "danger"
            );

        }


        // =================================
        // AI CONFIDENCE
        // =================================

        confidenceElement.textContent =
            ai.confidence
            + "%";


        // =================================
        // AI RECOMMENDATION
        // =================================

        recommendationElement.textContent =
            ai.recommendation;


        // =================================
        // AUTONOMOUS DECISION
        // =================================

        decisionElement.textContent =
            ai.decision;


        // =================================
        // AUTONOMOUS ACTION
        // =================================

        actionElement.textContent =
            ai.action;


        // =================================
        // REASONING TRAIL
        // =================================
        // Rests on VERIFY when nominal (LOW risk), ACT when
        // the AI is actively responding to a fault (MEDIUM/HIGH).

        const restingStage =
            ai.risk_level === "LOW" ? "verify" : "act";

        animateReasoningTrail(restingStage);


        // =================================
        // STABILIZING BANNER
        // =================================
        // Detects the MEDIUM/HIGH -> LOW transition (fault just
        // cleared) and shows a brief "stabilizing" message so the
        // VERIFY step has something visible to say, instead of
        // the dashboard silently snapping back to nominal.

        maybeShowStabilizingBanner(ai.risk_level);


        // =================================
        // ML ANOMALY DETECTION
        // =================================
        // Separate system from AERIS above. Guards against
        // mlAnomaly being missing/undefined so a stale page
        // load (before app.py was updated) doesn't throw and
        // break the rest of the dashboard update.

        if (mlAnomaly) {

            if (!mlAnomaly.model_ready) {

                mlAnomalyMessageElement.textContent =
                    "Model not yet trained.";

                mlAnomalyScoreElement.textContent =
                    "--";

                mlAnomalyStatusElement.textContent =
                    "N/A";

            }

            else {

                mlAnomalyMessageElement.textContent =
                    mlAnomaly.is_anomaly
                        ? "Anomalous telemetry pattern detected."
                        : "Telemetry pattern within normal range.";


                mlAnomalyScoreElement.textContent =
                    Number(
                        mlAnomaly.anomaly_score
                    ).toFixed(1)
                    + " / 100";

                mlAnomalyScoreElement.className =
                    "";

                if (mlAnomaly.anomaly_score >= 60) {

                    mlAnomalyScoreElement.classList.add(
                        "danger"
                    );

                }

                else if (mlAnomaly.anomaly_score >= 40) {

                    mlAnomalyScoreElement.classList.add(
                        "warning"
                    );

                }

                else {

                    mlAnomalyScoreElement.classList.add(
                        "safe"
                    );

                }


                mlAnomalyStatusElement.textContent =
                    mlAnomaly.is_anomaly
                        ? "ANOMALOUS"
                        : "NORMAL";

                mlAnomalyStatusElement.className =
                    "";

                mlAnomalyStatusElement.classList.add(
                    mlAnomaly.is_anomaly ? "danger" : "safe"
                );

            }

        }


        // =================================
        // PRESSURE GRAPH
        // =================================

        pressureChart
            .data
            .datasets[0]
            .data
            .shift();


        pressureChart
            .data
            .datasets[0]
            .data
            .push(
                engine.chamber_pressure_bar
            );


        pressureChart.update(
            "none"
        );


        // =================================
        // EVENT LOG
        // =================================

        updateEventLog(
            telemetry.events
        );


    }

    catch (error) {

        console.error(
            "Telemetry update failed:",
            error
        );

    }

}


// =====================================
// EVENT LOG
// =====================================

function updateEventLog(events) {

    const eventLog =
        document.getElementById(
            "eventLog"
        );


    if (!eventLog) {

        return;

    }


    eventLog.innerHTML =
        "";


    events
        .slice()
        .reverse()
        .forEach(
            event => {


                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "event-card "
                    +
                    event.level.toLowerCase();


                const header =
                    document.createElement(
                        "div"
                    );


                header.className =
                    "event-header";


                const level =
                    document.createElement(
                        "span"
                    );


                level.className =
                    "event-level";


                level.textContent =
                    event.level;


                header.appendChild(
                    level
                );


                if (
                    event.mission_time !== null
                    &&
                    event.mission_time !== undefined
                ) {

                    const timeSpan =
                        document.createElement(
                            "span"
                        );

                    timeSpan.className =
                        "event-time";

                    timeSpan.textContent =
                        "T+" + event.mission_time + "s";

                    header.appendChild(
                        timeSpan
                    );

                }


                const message =
                    document.createElement(
                        "p"
                    );


                message.textContent =
                    event.message;


                card.appendChild(
                    header
                );


                card.appendChild(
                    message
                );


                eventLog.appendChild(
                    card
                );

            }
        );

}


// =====================================
// START LIVE TELEMETRY
// =====================================

updateDashboard();


setInterval(
    updateDashboard,
    1000
);
// =====================================
// FAULT INJECTION CONTROLS
// =====================================

const activeFaultNameElement =
    document.getElementById("activeFaultName");


async function injectFault(faultName) {

    try {

        const response =
            await fetch("/fault/" + faultName);

        if (!response.ok) {

            throw new Error(
                "Fault injection failed"
            );

        }

        activeFaultNameElement.textContent =
            faultName.toUpperCase();

        // Immediately pull fresh telemetry so the
        // dashboard reacts without waiting up to 1s
        // for the next poll cycle.
        updateDashboard();

    }

    catch (error) {

        console.error(
            "Fault injection error:",
            error
        );

    }

}


async function clearFault() {

    try {

        const response =
            await fetch("/fault/clear");

        if (!response.ok) {

            throw new Error(
                "Fault clear failed"
            );

        }

        activeFaultNameElement.textContent =
            "None";

        updateDashboard();

    }

    catch (error) {

        console.error(
            "Fault clear error:",
            error
        );

    }

}