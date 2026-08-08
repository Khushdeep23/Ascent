events = []

last_message = None


def log_event(message, level, mission_time=None, checklist=None):

    global last_message

    if message == last_message:
        return

    last_message = message

    events.append({

        "message": message,

        "level": level,

        "mission_time": mission_time,

        "checklist": checklist or []

    })

    if len(events) > 12:
        events.pop(0)


def get_events():

    return events
