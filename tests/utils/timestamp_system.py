import unittest
import os
from datetime import datetime
from qililab.utils import timestamp_system as tsys

class TestFunctions(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = "test_data"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        # Clean up the temporary directory after testing
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_get_timestamp(self):
        timestamp = tsysget_timestamp()
        self.assertTrue(isinstance(timestamp, str))
        self.assertRegex(timestamp, r"\d{8}_\d{6}")

    def test_get_path_from_timestamp(self):
        timestamp = "20240101_120000"
        path = tsys.get_path_from_timestamp(timestamp, self.test_dir)
        self.assertIsNone(path)

        # Creating a mock folder structure for testing
        test_subdir = os.path.join(self.test_dir, timestamp)
        os.makedirs(test_subdir, exist_ok=True)
        with open(os.path.join(test_subdir, "example.yml"), "w") as f:
            f.write("example content")

        result_path = tsys.get_path_from_timestamp(timestamp, self.test_dir)
        self.assertEqual(result_path, os.path.join(test_subdir, "results.yml"))

    def test_get_timestamp_from_file(self):
        test_file_path = os.path.join(self.test_dir, "20240101_120000_example.yml")
        timestamp = tsys.get_timestamp_from_file(test_file_path)
        self.assertEqual(timestamp, "20240101_120000")

    def test_get_last_folder(self):
        os.makedirs(os.path.join(self.test_dir, "folder1"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "folder2"), exist_ok=True)
        last_folder = tsys.get_last_folder(self.test_dir)
        self.assertEqual(last_folder, "folder2")

    def test_get_last_timestamp(self):
        os.makedirs(os.path.join(self.test_dir, "20240101_120000"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "20240101_130000"), exist_ok=True)
        last_timestamp = tsys.get_last_timestamp(self.test_dir)
        self.assertEqual(last_timestamp, "20240101_130000")

    def test_get_last_results(self):
        last_day_folder = "20240101"
        full_day_path = os.path.join(self.test_dir, last_day_folder)
        os.makedirs(full_day_path, exist_ok=True)
        last_exp_folder = "120000"
        full_exp_path = os.path.join(full_day_path, last_exp_folder)
        os.makedirs(full_exp_path, exist_ok=True)
        with open(os.path.join(full_exp_path, "results.yml"), "w") as f:
            f.write("example content")

        results_path = tsys.get_last_results(self.test_dir)
        self.assertEqual(results_path, os.path.join(full_exp_path, "results.yml"))

if __name__ == "__main__":
    unittest.main()
