def analyze_engine(engine, limits):

    # =====================================
    # Read Engine Parameters
    # =====================================

    pressure = engine["chamber_pressure_bar"]
    temperature = engine["temperature_K"]
    vibration = engine["vibration_mm_s"]
    rpm = engine["rpm"]
    fuel_flow = engine["fuel_flow_kg_s"]
    health = engine["health"]


    # =====================================
    # FAULT DETECTION
    # =====================================
     # -------------------------
        # Engine Wear
        # -------------------------
    
    if health < limits["minimum_engine_health"]:
    
            confidence = min(
                99,
                70 + (
                    limits["minimum_engine_health"]
                    - health
                )
            )
    
            return {
                "status": "CRITICAL",
                "risk_level": "HIGH",
                "confidence": confidence,
    
                "diagnosis":
                    "Engine health below operational threshold.",
    
                "recommendation":
                    "Abort engine test.",
    
                "decision":
                    "ABORT",
    
                "action":
                    "Initiate engine test abort sequence."
            }
    

    # -------------------------
    # Cooling Failure
    # -------------------------

    if temperature > limits["max_temperature_K"]:

        confidence = min(
            99.0,
            70 + (
                temperature
                - limits["max_temperature_K"]
            ) / 10
        )

        return {
            "status": "CRITICAL",
            "risk_level": "HIGH",
            "confidence": round(confidence, 1),

            "diagnosis":
                "Cooling system efficiency appears degraded.",

            "recommendation":
                "Reduce engine thermal load immediately.",

            "decision":
                "COOLING_RESPONSE",

            "action":
                "Reduce engine throttle to 80% to lower thermal load."
        }


    # -------------------------
    # Turbopump Instability
    # -------------------------

    if (
        vibration > limits["max_vibration_mm_s"]
        or rpm > 28800
    ):

        confidence = 75

        if vibration > limits["max_vibration_mm_s"]:
            confidence += 10

        if rpm > 28800:
            confidence += 10

        confidence = min(
            confidence,
            99
        )

        return {
            "status": "WARNING",
            "risk_level": "MEDIUM",
            "confidence": confidence,

            "diagnosis":
                "Abnormal turbopump behavior detected.",

            "recommendation":
                "Monitor turbopump stability and inspect bearings.",

            "decision":
                "MONITOR",

            "action":
                "Continue operation while monitoring turbopump stability."
        }


    # -------------------------
    # Injector Blockage
    # -------------------------

    if (
        pressure > limits["max_chamber_pressure_bar"]
        and fuel_flow < 240
    ):

        return {
            "status": "CRITICAL",
            "risk_level": "HIGH",
            "confidence": 90,

            "diagnosis":
                "Possible injector blockage detected.",

            "recommendation":
                "Reduce throttle to 85% and inspect injector manifold.",

            "decision":
                "THROTTLE_REDUCTION",

            "action":
                "Reduce engine throttle to 85%."
        }


   

    # =====================================
    # NOMINAL OPERATION
    # =====================================

    return {
        "status": "NOMINAL",
        "risk_level": "LOW",
        "confidence": 99.2,

        "diagnosis":
            "Engine operating within nominal operating limits.",

        "recommendation":
            "Maintain current throttle.",

        "decision":
            "CONTINUE",

        "action":
            "Maintain current operating conditions."
    }