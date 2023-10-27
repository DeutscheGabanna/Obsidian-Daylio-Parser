"""Test cases for main.py"""
import unittest
import shutil # to delete temporary files
import subprocess # to run main.py
import os # to make temporary directories and join them

FILES = [
            "2022-10-25.md",
            "2022-10-26.md",
            "2022-10-27.md",
            "2022-10-30.md"
        ]
TEST_DIR = os.path.join(os.getcwd(), "_tests")
COMPUTED = os.path.join(TEST_DIR, "computed_results")
EXPECTED = os.path.join(TEST_DIR, "expected_results")

# TODO: maybe E2E testing be more integrated into workflow? you could launch main.py directly there
# run commands like cmp -s file1.txt file.txt afterwards to check if they're ok

class TestScript(unittest.TestCase):
    """Tests ../main.py"""
    def setUp(self):
        """Create temporary directory for test output files""" 
        if not os.path.exists(COMPUTED):
            os.mkdir(COMPUTED)

    def test_main(self):
        """Gives ../main.py a CSV file and checks whether it is identical to the expected_results"""
        if not subprocess.run(["python", "main.py", os.path.join(TEST_DIR, "testing_sheet.csv"), COMPUTED], check=True):
            self.fail()
        
        # Open each computed file and check if it's equal to the expected one
        for file in FILES:
            with open(os.path.join(EXPECTED, file), encoding="UTF-8") as expected_file, open(os.path.join(COMPUTED, file), encoding="UTF-8") as computed_file:
                self.assertListEqual(list(expected_file), list(computed_file))

    def tearDown(self):
        if os.path.isdir(COMPUTED):
            shutil.rmtree(COMPUTED)
        else:
            raise FileNotFoundError(f"{COMPUTED} is missing at teardown.")

# is this run as a main program, not component?
if __name__ == '__main__':
    unittest.main(argv=["first-arg-is-ignored"])
