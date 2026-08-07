import random



BASELINE_THRUST_KN = 742
BASELINE_FUEL_FLOW_KG_S = 245


TEMPERATURE_MIN_K = 3300
TEMPERATURE_MAX_K = 3550

RPM_MIN = 27000
RPM_MAX = 28700

VIBRATION_MIN_MM_S = 0
VIBRATION_MAX_MM_S = 4.0

PRESSURE_MIN_BAR = 90
PRESSURE_MAX_BAR = 102


# =====================================
# ENGINE SIMULATION
# =====================================

def update_engine(engine):   

    # ---------------------------------
    # Chamber Pressure
    # ---------------------------------

    engine["chamber_pressure_bar"] += random.uniform(
        -0.8,
        0.8
    )
# yha pe values clamp ho jati hai taki vo nornal se se bahar na aye aur 
# fault trigger na ho jaye
# kind of a guard band  
    engine["chamber_pressure_bar"] = max(
        PRESSURE_MIN_BAR,
        min(
            engine["chamber_pressure_bar"],
            PRESSURE_MAX_BAR
        )
    )


    # ---------------------------------
    # Temperature
    # ---------------------------------

    engine["temperature_K"] += random.randint(
        -20,
        20
    )

    engine["temperature_K"] = max(
        TEMPERATURE_MIN_K,
        min(
            engine["temperature_K"],
            TEMPERATURE_MAX_K
        )
    )


    # ---------------------------------
    # RPM
    # ---------------------------------

    engine["rpm"] += random.randint(
        -150,
        150
    )

    engine["rpm"] = max(
        RPM_MIN,
        min(
            engine["rpm"],
            RPM_MAX
        )
    )


    # ---------------------------------
    # Fuel Flow
    # ---------------------------------
   

    target_fuel_flow = BASELINE_FUEL_FLOW_KG_S * (
        engine.get("throttle_percent", 100) / 100
    )

    engine["fuel_flow_kg_s"] += random.uniform(-2, 2)

    # Pull gently back toward the throttle-correct target
    # so noise doesn't accumulate indefinitely.
    engine["fuel_flow_kg_s"] += (
        target_fuel_flow - engine["fuel_flow_kg_s"]
    ) * 0.1

    engine["fuel_flow_kg_s"] = max (0,round(
        engine["fuel_flow_kg_s"],
        1
    ))


    # ---------------------------------
    # Vibration
    # ---------------------------------

    engine["vibration_mm_s"] += random.uniform(
        -0.2,
        0.2
    )

    engine["vibration_mm_s"] = max(
        VIBRATION_MIN_MM_S,
        min(
            engine["vibration_mm_s"],
            VIBRATION_MAX_MM_S
        )
    )

    engine["vibration_mm_s"] = round(
        engine["vibration_mm_s"],
        2
    )


    return engine


# =====================================
# AERIS AUTONOMOUS ACTION
# =====================================


def apply_ai_action(engine, ai_result):
    # matlab basically jo bhi ai ne decide kara usse physically show karo 

    decision = ai_result["decision"]


    # =================================
    # CONTINUE
    # =================================

    if decision == "CONTINUE":

        engine["throttle_percent"] = 100


    # =================================
    # THROTTLE REDUCTION
    # =================================

    elif decision == "THROTTLE_REDUCTION":

        engine["throttle_percent"] = 85


    # =================================
    # COOLING RESPONSE
    # =================================

    elif decision == "COOLING_RESPONSE":

        engine["throttle_percent"] = 80

        # Reduced thermal load — this is a one-time
        # correction nudge, not compounding, since
        # update_engine() re-randomizes temperature
        # within bounds on the next cycle anyway.
        engine["temperature_K"] = max(
            TEMPERATURE_MIN_K,
            engine["temperature_K"] - 50
        )


    # =================================
    # MONITOR
    # =================================

    elif decision == "MONITOR":

        engine["throttle_percent"] = 100


    # =================================
    # ABORT
    # =================================

    elif decision == "ABORT":

        engine["throttle_percent"] = 0


    # =================================
    # APPLY THROTTLE TO THRUST & FUEL
    # =================================
    # Single source of truth: thrust and fuel flow are
    # ALWAYS derived from baseline * current throttle.
    # This runs regardless of which branch fired above,
    # so thrust/fuel_flow can never drift independently
    # of throttle_percent.

    throttle_fraction = engine["throttle_percent"] / 100

    engine["thrust_kN"] = round(
        BASELINE_THRUST_KN * throttle_fraction,
        1
    )

    return engine