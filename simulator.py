"""Software simulator of the ESP32 plant node."""
import random

class PlantNode:
    def __init__(self, seed=1, moisture=55.0, dry_rate=0.35, water_rate=2.0):
        self.rng = random.Random(seed)
        self.moisture = float(moisture)
        self.pump_on = False
        self.dry_rate = dry_rate
        self.water_rate = water_rate

    def step(self):
        if self.pump_on:
            self.moisture += self.water_rate
        else:
            self.moisture -= self.dry_rate * self.rng.uniform(0.6, 1.4)
        self.moisture = max(0.0, min(100.0, self.moisture))
        return {
            "temperature": round(self.rng.uniform(26, 34), 1),
            "humidity": round(self.rng.uniform(45, 70), 1),
            "soil_moisture": round(self.moisture, 1),
            "pump_on": self.pump_on,
        }
