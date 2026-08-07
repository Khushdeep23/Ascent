from flask import Flask, render_template, jsonify
import json
import time

from ai.analyzer import analyze_engine
from ai.logger import log_event, get_events
from ai.anomaly_detector import score_anomaly

from telemetry.simulator import (
    update_engine,
    apply_ai_action
)

from telemetry.faults import (
    apply_fault,
    set_fault,
    clear_fault
)


app = Flask(__name__)


# =====================================
# MISSION TIMER
# =====================================

START_TIME = time.time()


# =====================================
# LOAD INITIAL SYSTEM STATE
# =====================================

with open("telemetry/engine_data.json", "r") as file:
    SYSTEM_STATE = json.load(file)


# =====================================
# TELEMETRY PROCESSING PIPELINE
# =====================================

def process_telemetry():

    global SYSTEM_STATE

    telemetry = SYSTEM_STATE


    # =================================
    # 1. Simulate Engine
    # =================================

    telemetry["engine"] = update_engine(
        telemetry["engine"]
    )


    # =================================
    # 2. Apply Active Fault
    # =================================

    telemetry["engine"] = apply_fault(
        telemetry["engine"]
    )


    # =================================
    # 3. ML Anomaly Detection
    # =================================
    # Runs on the fault-affected reading, same as the rule-based
    # analyzer below sees. This is the trained Isolation Forest,
    # separate from and running alongside the rule-based diagnosis
    # — not replacing it. If anomaly_model.pkl hasn't been trained
    # yet, this returns a safe "not ready" placeholder instead of
    # crashing the app.

    telemetry["ml_anomaly"] = score_anomaly(
        telemetry["engine"]
    )


    # =================================
    # 4. Update Mission Timer
    # =================================

    telemetry["mission"]["mission_time"] = int(
        time.time() - START_TIME
    )


    # =================================
    # 5. AERIS AI Analysis
    # =================================

    ai_result = analyze_engine(
        telemetry["engine"],
        telemetry["limits"]
    )

    telemetry["ai"] = ai_result


    # =================================
    # 6. Update Engine Status
    # =================================

    telemetry["engine"]["status"] = (
        ai_result["status"]
    )


    # =================================
    # 7. Autonomous AI Action
    # =================================

    telemetry["engine"] = apply_ai_action(
        telemetry["engine"],
        ai_result
    )


    # =================================
    # 8. Log AI Decision
    # =================================
    # mission_time is passed through so each event card can show
    # when it happened (e.g. "T+42s"), not just the message + level.

    log_event(
        ai_result["diagnosis"],
        ai_result["risk_level"],
        telemetry["mission"]["mission_time"]
    )


    # =================================
    # 9. Load Event History
    # =================================

    telemetry["events"] = get_events()


    # =================================
    # 10. Save Updated State
    # =================================

    SYSTEM_STATE = telemetry


    # =================================
    # Return Complete System State
    # =================================

    return telemetry


# =====================================
# DASHBOARD
# =====================================

@app.route("/")
def home():

    telemetry = process_telemetry()

    return render_template(
        "index.html",
        telemetry=telemetry
    )


# =====================================
# LIVE TELEMETRY API
# =====================================

@app.route("/telemetry")
def telemetry():

    telemetry = process_telemetry()

    return jsonify(telemetry)


# =====================================
# FAULT INJECTION
# =====================================

@app.route("/fault/<fault_name>")
def inject_fault(fault_name):

    set_fault(fault_name)

    return jsonify({
        "status": "success",
        "fault": fault_name
    })


# =====================================
# CLEAR ACTIVE FAULT
# =====================================

@app.route("/fault/clear")
def remove_fault():

    clear_fault()

    return jsonify({
        "status": "cleared"
    })


# =====================================
# START APPLICATION
# =====================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5001
        
    )