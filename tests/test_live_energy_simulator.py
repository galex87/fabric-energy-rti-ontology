import random
import unittest

from simulator.live_energy_simulator import classify_alert, generate_event


class TestLiveEnergySimulator(unittest.TestCase):
    def test_generate_event_shape_and_ranges(self):
        event = generate_event(random.Random(7), sequence=1)

        self.assertEqual(event["event_id"], 1)
        self.assertIn(event["site_id"], {"north-farm", "south-farm", "coastal-farm"})
        self.assertGreaterEqual(event["wind_mw"], 0.0)
        self.assertGreaterEqual(event["solar_mw"], 0.0)
        self.assertGreaterEqual(event["grid_demand_mw"], 80.0)
        self.assertLessEqual(event["grid_demand_mw"], 220.0)
        self.assertGreaterEqual(event["renewable_ratio"], 0.0)
        self.assertLessEqual(event["renewable_ratio"], 1.0)
        self.assertIn(event["alert_level"], {"normal", "warning", "critical"})

    def test_classify_alert_thresholds(self):
        self.assertEqual(classify_alert(0.2, 180, 420), "critical")
        self.assertEqual(classify_alert(0.35, 120, 350), "warning")
        self.assertEqual(classify_alert(0.6, 120, 260), "normal")


if __name__ == "__main__":
    unittest.main()
