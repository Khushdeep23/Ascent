import random


# =====================================
# BASELINE HEALTH REFERENCE
# =====================================


BASELINE_HEALTH = 97


# =====================================
# ACTIVE FAULT STATE
# =====================================

active_fault = None


# =====================================
# SET ACTIVE FAULT
# =====================================

def set_fault(fault_name):

    global active_fault

    active_fault = fault_name


# =====================================
# CLEAR ACTIVE FAULT
# =====================================

def clear_fault():

    global active_fault

    active_fault = None


# =====================================
# GET ACTIVE FAULT
# =====================================

def get_active_fault():

    return active_fault


# =====================================
# APPLY ACTIVE FAULT TO ENGINE
# =====================================

def apply_fault(engine):

    # ---------------------------------
    # No active fault
    # ---------------------------------
    # Every other telemetry field (temperature, pressure, RPM,
    # vibration, fuel flow) already self-corrects every cycle
    # inside update_engine() in simulator.py, fault or no fault.
    # Health was the one field with no recovery path at all —
    # once cooling/wear degraded it, it stayed degraded forever,
    # even after the fault was cleared. This gently regenerates
    # it back toward baseline, same damped-drift approach used
    # for fuel flow in Phase 1, so it recovers visibly but not
    # instantly.

    if active_fault is None:

        if engine["health"] < BASELINE_HEALTH:

            engine["health"] += 0.8

            engine["health"] = min(
                engine["health"],
                BASELINE_HEALTH
            )

        return engine


    # =================================
    # INJECTOR BLOCKAGE
    # =================================

    if active_fault == "injector":

        # Reduced fuel flow
        engine["fuel_flow_kg_s"] -= random.uniform(
            2,
            4
        )

        # Poor combustion increases temperature
        engine["temperature_K"] += random.randint(
            20,
            40
        )

        # Pressure instability
        engine["chamber_pressure_bar"] += random.uniform(
            3.5,
            5.0
        )


    # =================================
    # COOLING FAILURE
    # =================================

    elif active_fault == "cooling":

        # Rapid thermal increase
        engine["temperature_K"] += random.randint(
            40,
            80
        )

        # Progressive engine degradation
        engine["health"] -= 1


    # =================================
    # TURBOPUMP INSTABILITY
    # =================================

    elif active_fault == "pump":

        # RPM instability
        engine["rpm"] += random.randint(
            150,
            350
        )

        # Increased vibration
        engine["vibration_mm_s"] += random.uniform(
            0.3,
            0.8
        )


    # =================================
    # ENGINE WEAR
    # =================================

    elif active_fault == "wear":

        # Progressive health degradation
        engine["health"] -= random.uniform(
            0.5,
            1.5
        )

        # Slight increase in vibration
        engine["vibration_mm_s"] += random.uniform(
            0.1,
            0.3
        )


    # =================================
    # SAFETY CLAMPS
    # =================================
   #values ko negative jane me rokta hai 
    engine["health"] = max(
        engine["health"],
        0
    )

    engine["health"] = min(
        engine["health"],
        BASELINE_HEALTH
    )

    engine["temperature_K"] = max(
        engine["temperature_K"],
        0
    )

    engine["fuel_flow_kg_s"] = max(
        engine["fuel_flow_kg_s"],
        0
    )

    engine["rpm"] = max(
        engine["rpm"],
        0
    )

    engine["vibration_mm_s"] = max(
        engine["vibration_mm_s"],
        0
    )


    return engine