import unittest
from utils import alert, alert_fixed, check_sms_status, config, logging_config

class TestAlert(unittest.TestCase):
    def test_alert_send(self):
        self.assertTrue(hasattr(alert, "send_alert"))

class TestAlertFixed(unittest.TestCase):
    def test_alert_fixed_send(self):
        self.assertTrue(hasattr(alert_fixed, "send_alert"))

class TestCheckSMSStatus(unittest.TestCase):
    def test_check_sms(self):
        self.assertTrue(hasattr(check_sms_status, "check_status"))

class TestConfig(unittest.TestCase):
    def test_config_load(self):
        self.assertTrue(hasattr(config, "load_config"))

class TestLoggingConfig(unittest.TestCase):
    def test_logging_setup(self):
        self.assertTrue(hasattr(logging_config, "setup_logging"))

if __name__ == "__main__":
    unittest.main()
