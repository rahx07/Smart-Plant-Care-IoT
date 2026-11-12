import json
import tempfile
import unittest
from pathlib import Path

import database as db
from controller import decide, moisture_percent
from simulator import PlantNode
from mqtt_bridge import handle_message

class SmartPlantTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")
        db.create_tables(self.db_path)
        db.ensure_device("plant01", "Test pot", self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_device_and_reading(self):
        db.add_reading("plant01", 25, 50, 45, False, path=self.db_path)
        self.assertIsNotNone(db.latest_reading("plant01", self.db_path))

    def test_moisture_conversion(self):
        self.assertEqual(moisture_percent(3200), 0.0)
        self.assertEqual(moisture_percent(1300), 100.0)

    def test_dry_soil_turns_pump_on(self):
        self.assertTrue(decide(20, 25, False)[0])

    def test_moisture_threshold_turns_pump_off(self):
        self.assertFalse(decide(60, 25, True)[0])

    def test_heat_lock(self):
        self.assertFalse(decide(20, 40, False)[0])

    def test_safety_timeout(self):
        self.assertFalse(decide(40, 25, True, 120)[0])

    def test_bridge_logs_reading(self):
        commands = []
        payload = json.dumps({"temp": 28, "hum": 50, "soil": 20, "pump": 0})
        result = handle_message(
            "plant01", payload, lambda topic, message: commands.append((topic, message)),
            {}, self.db_path
        )
        self.assertEqual(result, "command")
        self.assertEqual(commands[0][1], "ON")

    def test_bad_message_ignored(self):
        self.assertEqual(
            handle_message("plant01", "{bad json", lambda *args: None, {}, self.db_path),
            "ignored"
        )

    def test_simulator_stays_in_range(self):
        node = PlantNode()
        self.assertGreaterEqual(node.step()["soil_moisture"], 0)

if __name__ == "__main__":
    unittest.main()
