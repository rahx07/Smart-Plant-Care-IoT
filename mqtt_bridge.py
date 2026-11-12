"""MQTT bridge: telemetry in -> SQLite -> decision -> pump command out."""
import json
import database as db
from controller import decide

def handle_message(device_id, payload, publish, state, path=None):
    """Process one telemetry payload. publish(topic, text) sends pump commands."""
    try:
        data = json.loads(payload)
        temperature = float(data["temp"])
        humidity = float(data["hum"])
        moisture = float(data["soil"])
        pump_on = bool(int(data["pump"])) if isinstance(data["pump"], (int, float, str)) else bool(data["pump"])
        if not (0 <= moisture <= 100):
            return "ignored"
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return "ignored"

    db.ensure_device(device_id, "ESP32 plant", path=path)
    db.add_reading(device_id, temperature, humidity, moisture, pump_on, path=path)
    state["run"] = state.get("run", 0) + 5 if pump_on else 0
    want, reason = decide(moisture, temperature, pump_on, state["run"])
    if want != pump_on:
        publish(f"smartplant/{device_id}/pump", "ON" if want else "OFF")
        db.log_event(device_id, "PUMP_ON" if want else "PUMP_OFF", reason, path=path)
        return "command"
    return "logged"

def run(host="localhost", device_id="plant01"):
    import paho.mqtt.client as mqtt
    db.create_tables()
    db.ensure_device(device_id, "ESP32 plant")
    state = {}
    client = mqtt.Client()
    client.on_message = lambda client_obj, userdata, msg: handle_message(
        device_id, msg.payload.decode("utf-8"), client_obj.publish, state
    )
    client.connect(host, 1883)
    client.subscribe(f"smartplant/{device_id}/telemetry")
    print(f"Listening for telemetry on {host}:1883")
    client.loop_forever()

if __name__ == "__main__":
    run()
