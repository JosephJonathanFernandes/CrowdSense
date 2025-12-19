import unittest
from simulation import crowdsense_simulation, simulation, trigger_disaster

class TestCrowdSenseSimulation(unittest.TestCase):
    def test_simulation_main(self):
        self.assertTrue(hasattr(crowdsense_simulation, "main"))

class TestSimulation(unittest.TestCase):
    def test_simulation_class(self):
        self.assertTrue(hasattr(simulation, "Simulation"))

class TestTriggerDisaster(unittest.TestCase):
    def test_trigger_function(self):
        self.assertTrue(callable(trigger_disaster.trigger_disaster))

if __name__ == "__main__":
    unittest.main()
