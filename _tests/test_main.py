"""Test cases for main.py"""
import unittest
import shutil # to delete temporary files
import subprocess # to run main.py
import os # to make temporary directories and join them

# import csv
# # Custom
# import parse_csv
# import utils

# class TestScript(unittest.TestCase):
#     def test_expanded_path(self):
#         self.assertEqual(
#             utils.expand_path(r"./_tests/testing_sheet.csv"),
#             r"/home/deutschegabanna/Obsidian-Daylio-Parser/_tests/testing_sheet.csv"
#         )

#     def test_this_row(self, row_to_parse, time, mood, activities, title, note):
#         """Checks if Entry object correctly parses CSV row and populates its parameters.
#         time, mood, activities, title, and note in function arguments should be the expected values."""
#         tmp_entry = parse_csv.Entry(csv.reader([row_to_parse], delimiter=',', quotechar='"'))
#         self.assertEqual(tmp_entry.time, time, "Entry created with wrong time.")
#         self.assertEqual(tmp_entry.mood, mood, "Entry created with wrong mood.")
#         self.assertListEqual(tmp_entry.activities, activities, "Entry created with wrong activities array.")
#         self.assertEqual(tmp_entry.title, title, "Entry created with wrong title.")
#         self.assertEqual(tmp_entry.note, note, "Entry created with wrong note.")

#     def test_parsing(self):
#         """Check several rows to trigger test_this_row for each of them."""
#         # Sample entry
#         self.test_this_row(
#             "2022-10-30,October 30,Sunday,10:04 AM,vaguely ok,2ćities  skylines | dó#lóó fa$$s_ą%,\"Dolomet\",\"Lorem ipsum sit dolomet amęt.\"",
#             "10:04 AM",
#             "vaguely ok",
#             ["2ćities-skylines", "dólóó-fas_ą"],
#             "Dolomet",
#             "Lorem ipsum sit dolomet amęt."
#         )
#         # Sample entry
#         self.test_this_row(
#             "2022-10-27,October 27,Thursday,1:49 PM,vaguely good,chess,\"Cras pretium\",\"Lorem ipsum dolor sit amet, consectetur adipiscing elit.\"",
#             "1:49 PM",
#             "vaguely good",
#             ["chess"],
#             "Cras pretium",
#             "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
#         )
#         # Sample entry
#         self.test_this_row(
#             "2022-10-29,October 29,Saturday,3:30 PM,happy,drawing,\"Art session\",\"Had a great time drawing today.\"",
#             "3:30 PM",
#             "happy",
#             ["drawing"],
#             "Art session",
#             "Had a great time drawing today."
#         )
#         # Sample entry
#         self.test_this_row(
#             "2022-10-28,October 28,Wednesday,9:15 AM,sad,reading,\"A good book\",\"Enjoyed reading for a while.\"",
#             "9:15 AM",
#             "sad",
#             ["reading"],
#             "A good book",
#             "Enjoyed reading for a while."
#         )

    
#     def test_parsing_incomplete_data(self):
#         """Check if Entry object correctly consumes an array with incomplete data"""
#         sample_row = [
#             "2022-10-30",
#             "October 30",
#             "Sunday",
#             "10:04 AM",
#             "vaguely ok"
#         ]
#         try:
#             sample_entry = parse_csv.Entry(sample_row)
#         except IndexError:
#             pass
#         else:
#             pass

FILES = [
            "2022-10-25.md",
            "2022-10-26.md",
            "2022-10-27.md",
            "2022-10-30.md"
        ]
TEST_DIR = os.path.join(os.getcwd(), "_tests")
COMPUTED = os.path.join(TEST_DIR, "computed_results")
EXPECTED = os.path.join(TEST_DIR, "expected_results")

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
