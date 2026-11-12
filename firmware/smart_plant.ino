// ESP32 firmware: DHT22 GPIO4, soil sensor GPIO34, relay GPIO26.
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASS = "YOUR_PASSWORD";
const char* BROKER = "192.168.1.10"; // Replace with your PC's LAN IP
const char* DEVICE = "plant01";

const int SOIL_PIN = 34;
const int RELAY_PIN = 26;
const int DRY_ADC = 3200;
const int WET_ADC = 1300;
const unsigned long MAX_RUN_MS = 120000;

DHT dht(4, DHT22);
WiFiClient net;
PubSubClient mqtt(net);
bool pumpOn = false;
unsigned long pumpStart = 0;
unsigned long lastSend = 0;

String telemetryTopic = String("smartplant/") + DEVICE + "/telemetry";
String pumpTopic = String("smartplant/") + DEVICE + "/pump";

void setPump(bool on) {
  pumpOn = on;
  digitalWrite(RELAY_PIN, on ? LOW : HIGH); // Active-low relay
  if (on) pumpStart = millis();
}

void onMessage(char* topic, byte* payload, unsigned int len) {
  String command;
  for (unsigned int i = 0; i < len; i++) command += (char)payload[i];
  command.trim();
  if (command == "ON") setPump(true);
  else if (command == "OFF") setPump(false);
}

void connectAll() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) delay(500);
  }
  while (!mqtt.connected()) {
    if (mqtt.connect(DEVICE)) mqtt.subscribe(pumpTopic.c_str());
    else delay(2000);
  }
}

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  setPump(false);
  dht.begin();
  mqtt.setServer(BROKER, 1883);
  mqtt.setCallback(onMessage);
  connectAll();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED || !mqtt.connected()) connectAll();
  mqtt.loop();

  if (pumpOn && millis() - pumpStart >= MAX_RUN_MS) setPump(false);

  if (millis() - lastSend >= 5000) {
    lastSend = millis();
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    int raw = analogRead(SOIL_PIN);
    float soil = constrain(
      (DRY_ADC - raw) * 100.0 / (DRY_ADC - WET_ADC), 0, 100
    );

    if (!isnan(temperature) && !isnan(humidity)) {
      char message[120];
      snprintf(message, sizeof(message),
        "{\"temp\":%.1f,\"hum\":%.1f,\"soil\":%.1f,\"pump\":%d}",
        temperature, humidity, soil, pumpOn ? 1 : 0);
      mqtt.publish(telemetryTopic.c_str(), message);
    }
  }
}
