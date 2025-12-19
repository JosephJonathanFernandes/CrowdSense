import unittest
from core import anomaly_detection
from core import crowdsense_enhanced
from core import database
from core import location_extraction
from core import scheduler

class TestAnomalyDetection(unittest.TestCase):
    def test_detector_init(self):
        detector = anomaly_detection.AnomalyDetector(window_size=5, ewma_alpha=0.3, z_threshold=2.0)
        self.assertIsNotNone(detector)

class TestDatabase(unittest.TestCase):
    def test_db_init(self):
        db = database.Database(':memory:')
        self.assertIsNotNone(db)

class TestLocationExtraction(unittest.TestCase):
    def test_extract_location(self):
        result = location_extraction.extract_location("Fire in New York")
        self.assertIsInstance(result, dict)

class TestScheduler(unittest.TestCase):
    def test_scheduler_add_task(self):
        sched = scheduler.TaskScheduler()
        def dummy(): pass
        sched.add_task(name="dummy", func=dummy, interval_minutes=1)
        self.assertIn("dummy", sched.tasks)

if __name__ == "__main__":
    unittest.main()
