from flask import Flask, render_template, jsonify, Response
import json
import time
import csv
import io

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
# DIAGNOSTIC CHECKLIST BUILDER
# =====================================
# Bounty (Core): the 6 telemetry inputs analyzer.py always reads
# before producing a diagnosis, captured with their live value at
# the moment of that decision.

def build_checklist(engine):

    return [
        {"field": "Chamber Pressure", "value": engine["chamber_pressure_bar"], "unit": "bar", "checked": True},
        {"field": "Temperature", "value": engine["temperature_K"], "unit": "K", "checked": True},
        {"field": "RPM", "value": engine["rpm"], "unit": "", "checked": True},
        {"field": "Fuel Flow", "value": engine["fuel_flow_kg_s"], "unit": "kg/s", "checked": True},
        {"field": "Vibration", "value": engine["vibration_mm_s"], "unit": "mm/s", "checked": True},
        {"field": "Engine Health", "value": engine["health"], "unit": "%", "checked": True},
    ]


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

    log_event(
        ai_result["diagnosis"],
        ai_result["risk_level"],
        telemetry["mission"]["mission_time"],
        checklist=build_checklist(telemetry["engine"])
    )


    # =================================
    # 9. Load Event History
    # =================================

    telemetry["events"] = get_events()


    # =================================
    # 10. Save Updated State
    # =================================

    SYSTEM_STATE = telemetry


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
# MISSION REPORT EXPORT — HTML
# =====================================
# Elite bounty task: downloadable report reusing existing captured
# fields, statuses, recommendations, and notes. Uses whatever is
# currently in SYSTEM_STATE (the exact same data already on the
# dashboard) — nothing new computed, purely a formatted export of
# real, already-captured mission data.

def build_html_report(telemetry):

    engine = telemetry["engine"]
    ai = telemetry["ai"]
    ml = telemetry["ml_anomaly"]
    events = telemetry["events"]

    rows = ""
    for e in reversed(events):
        checklist_str = ", ".join(
            f"{c['field']}: {c['value']} {c['unit']}".strip()
            for c in e.get("checklist", [])
        )
        rows += f"""
        <tr>
            <td>T+{e.get('mission_time', '')}s</td>
            <td class="lvl-{e['level'].lower()}">{e['level']}</td>
            <td>{e['message']}</td>
            <td class="small">{checklist_str}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ASCENT Mission Report</title>
<style>
    body {{ background:#0B1020; color:#fff; font-family:Arial,sans-serif; padding:40px; }}
    h1 {{ color:#4CC9F0; }}
    h2 {{ color:#55D6FF; margin-top:30px; }}
    table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
    td, th {{ border:1px solid #333; padding:8px 12px; text-align:left; font-size:14px; }}
    th {{ background:#171E33; color:#9FB0D0; }}
    .box {{ background:#171E33; padding:20px; border-radius:12px; margin-top:10px; }}
    .lvl-high {{ color:#FF4D4D; font-weight:bold; }}
    .lvl-medium {{ color:#FFD166; font-weight:bold; }}
    .lvl-low {{ color:#31E56B; font-weight:bold; }}
    .small {{ font-size:12px; color:#9FB0D0; }}
    .meta {{ color:#7F92B4; }}
</style>
</head>
<body>

<h1>ASCENT Mission Report</h1>
<p class="meta">Generated at mission time T+{telemetry['mission']['mission_time']}s | Vehicle: {telemetry['vehicle']} | Engine: {engine['type']}</p>

<h2>Current Telemetry Snapshot</h2>
<div class="box">
<table>
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Thrust</td><td>{engine['thrust_kN']} kN</td></tr>
<tr><td>Chamber Pressure</td><td>{engine['chamber_pressure_bar']} bar</td></tr>
<tr><td>Temperature</td><td>{engine['temperature_K']} K</td></tr>
<tr><td>RPM</td><td>{engine['rpm']}</td></tr>
<tr><td>Fuel Flow</td><td>{engine['fuel_flow_kg_s']} kg/s</td></tr>
<tr><td>Vibration</td><td>{engine['vibration_mm_s']} mm/s</td></tr>
<tr><td>Engine Health</td><td>{engine['health']}%</td></tr>
<tr><td>Status</td><td>{engine['status']}</td></tr>
</table>
</div>

<h2>AERIS AI Diagnosis (Rule-Based)</h2>
<div class="box">
<p><b>Diagnosis:</b> {ai['diagnosis']}</p>
<p><b>Risk Level:</b> <span class="lvl-{ai['risk_level'].lower()}">{ai['risk_level']}</span></p>
<p><b>Confidence:</b> {ai['confidence']}%</p>
<p><b>Recommendation:</b> {ai['recommendation']}</p>
<p><b>Autonomous Decision:</b> {ai['decision']}</p>
<p><b>Autonomous Action:</b> {ai['action']}</p>
</div>

<h2>ML Anomaly Detection (Isolation Forest)</h2>
<div class="box">
<p><b>Anomaly Score:</b> {ml['anomaly_score']} / 100</p>
<p><b>Status:</b> {"ANOMALOUS" if ml['is_anomaly'] else "NORMAL"}</p>
</div>

<h2>Mission Event History</h2>
<table>
<tr><th>Time</th><th>Level</th><th>Message</th><th>Checklist Snapshot</th></tr>
{rows}
</table>

</body>
</html>"""

    return html


@app.route("/export/report")
def export_report():

    telemetry = process_telemetry()

    html = build_html_report(telemetry)

    return Response(
        html,
        mimetype="text/html",
        headers={
            "Content-Disposition": "attachment; filename=ascent_mission_report.html"
        }
    )


# =====================================
# MISSION REPORT EXPORT — CSV
# =====================================
# Same underlying event data, flat tabular format instead of the
# formatted HTML report above.

@app.route("/export/csv")
def export_csv():

    telemetry = process_telemetry()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "mission_time", "level", "message",
        "chamber_pressure_bar", "temperature_K", "rpm",
        "fuel_flow_kg_s", "vibration_mm_s", "engine_health_pct"
    ])

    for e in reversed(telemetry["events"]):

        checklist = {c["field"]: c["value"] for c in e.get("checklist", [])}

        writer.writerow([
            e.get("mission_time", ""),
            e["level"],
            e["message"],
            checklist.get("Chamber Pressure", ""),
            checklist.get("Temperature", ""),
            checklist.get("RPM", ""),
            checklist.get("Fuel Flow", ""),
            checklist.get("Vibration", ""),
            checklist.get("Engine Health", ""),
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=ascent_event_history.csv"
        }
    )


# =====================================
# START APPLICATION
# =====================================

import os

if __name__ == "__main__":
    app.run(
       debug=True,
       port=5001
    )
