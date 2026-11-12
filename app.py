"""Smart Plant Care - Streamlit dashboard. Run: streamlit run app.py"""
from datetime import date
import pandas as pd
import streamlit as st
import database as db
from controller import decide
from simulator import PlantNode

DEVICE = "plant01"
st.set_page_config(page_title="Smart Plant Care", page_icon="🌱", layout="wide")
db.create_tables()
db.ensure_device(DEVICE, "Balcony pot")

def dashboard():
    st.title("🌱 Smart Plant Care - Dashboard")
    last = db.latest_reading(DEVICE)
    if not last:
        st.info("No data yet. Run the Simulator or start the MQTT bridge with ESP32 hardware.")
        return
    a, b, c, d = st.columns(4)
    a.metric("Soil moisture", f"{last['soil_moisture']:.1f}%")
    b.metric("Temperature", f"{last['temperature']:.1f} °C")
    c.metric("Humidity", f"{last['humidity']:.1f}%")
    d.metric("Pump", "ON" if last["pump_on"] else "OFF")
    readings = db.get_readings(DEVICE, limit=500)
    if readings:
        frame = pd.DataFrame(readings)
        st.subheader("Soil moisture history")
        st.line_chart(frame.set_index("ts")["soil_moisture"])
        st.dataframe(frame.tail(20), use_container_width=True, hide_index=True)

def simulator():
    st.title("🧪 Simulator (no hardware needed)")
    st.write("Simulate sensor readings and automatic irrigation decisions on your PC.")
    steps = st.slider("Number of simulated readings", 50, 600, 300, 50)
    low, high = st.slider("Pump ON below / OFF at (%)", 10, 90, (30, 60))
    if st.button("Run simulation", type="primary"):
        node = PlantNode()
        run_seconds = 0
        db.ensure_device(DEVICE, "Balcony pot")
        for _ in range(steps):
            reading = node.step()
            run_seconds = run_seconds + 5 if reading["pump_on"] else 0
            want, reason = decide(
                reading["soil_moisture"], reading["temperature"],
                reading["pump_on"], run_seconds, low, high
            )
            if want != node.pump_on:
                db.log_event(
                    DEVICE, "PUMP_ON" if want else "PUMP_OFF", reason
                )
            node.pump_on = want
            db.add_reading(
                DEVICE, reading["temperature"], reading["humidity"],
                reading["soil_moisture"], node.pump_on
            )
        st.success(f"Simulation complete: {steps} readings saved to SQLite.")
        st.info("Open Dashboard or History to view the results.")

def history():
    st.title("📚 History and Reports")
    selected_day = st.date_input("Select date", date.today())
    summary = db.daily_summary(DEVICE, selected_day.isoformat())
    st.subheader("Daily summary")
    st.json(summary)
    events = db.get_events(DEVICE, limit=500)
    if events:
        frame = pd.DataFrame(events)
        st.subheader("Pump events")
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button(
            "Download events CSV", frame.to_csv(index=False).encode("utf-8"),
            f"events_{selected_day.isoformat()}.csv", "text/csv"
        )
    else:
        st.info("No pump events recorded yet.")

pages = {
    "Dashboard": dashboard,
    "Simulator": simulator,
    "History": history,
}
st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Choose a page", list(pages))
pages[selected_page]()
