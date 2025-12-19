import unittest

class TestImports(unittest.TestCase):
    def test_imports(self):
        try:
            import core
            import simulation
            import utils
            import web
        except ImportError as e:
            self.fail(f"Import failed: {e}")

if __name__ == "__main__":
    unittest.main()
