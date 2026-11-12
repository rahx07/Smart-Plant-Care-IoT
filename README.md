# Smart Plant Care – IoT Automatic Irrigation

This project monitors soil moisture, air temperature and humidity. A rule-based controller decides when a pump should run. It includes a Streamlit dashboard and a software simulator that works without physical hardware.

## 1. Requirements
- Windows 10/11
- Python 3.10 or 3.11
- VS Code (recommended)

## 2. Run the simulator (no hardware required)
Open this folder in VS Code, then run these commands in the terminal:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501). Select **Simulator**, choose the number of readings, and click **Run simulation**. Then inspect Dashboard and History.

## 3. Run automated tests
```powershell
python -m unittest discover -s tests -v
```

## 4. Run with ESP32 hardware (advanced)
1. Install Mosquitto MQTT broker and Arduino IDE.
2. Install Arduino libraries: PubSubClient and DHT sensor library (plus Adafruit Unified Sensor if requested).
3. Edit `firmware/smart_plant.ino`: enter Wi-Fi SSID/password and the PC's LAN IP as `BROKER`.
4. Connect DHT22 data to GPIO4, capacitive soil sensor analog output to GPIO34, and relay input to GPIO26. Power the pump from a suitable separate supply.
5. Upload the firmware to ESP32.
6. Start Mosquitto, then run `python mqtt_bridge.py` in another terminal.

**Safety:** Test the relay and pump using a suitable low-voltage supply. Do not connect mains voltage unless qualified. Check your relay's active-low/active-high behavior and sensor calibration before operating a pump unattended.

## Control rules
- Pump turns ON when soil moisture is below 30%.
- Pump turns OFF at 60% moisture.
- New watering is postponed at temperatures of 38°C or above.
- Pump has a 120-second maximum run timeout.

The simulator uses illustrative drying/watering rates; they are not real soil measurements.
