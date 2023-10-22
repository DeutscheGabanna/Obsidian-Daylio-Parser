"""Test cases for main.py"""
import unittest
# Custom
import parse_csv
import utils

class TestScript(unittest.TestCase):
    def setUp(self):
        self.test_files_path = r"_tests/files"
        self.test_days = {
            "2022-10-30": [
                {
                    "time": "10:04 AM",
                    "mood": "vaguely ok",
                    "activites": [
                        "2ćities-skylines",
                        "dólóó-fas_ą"
                    ],
                    "title": "Dolomet",
                    "note": "Lorem ipsum sit dolomet amęt."
                },
            ],
            "2022-10-27": [
                {
                    "time": "1:49 PM",
                    "mood": "vaguely good",
                    "activites": [
                        "chess"
                    ],
                    "title": "Cras pretium",
                    "note": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
                },
                {
                    "time": "12:00 AM",
                    "mood": "fatigued",
                    "activites": [
                        "allegro",
                        "working remotely"
                    ],
                    "title": "Suspendisse sit amet",
                    "note": "Phaśellus pharetra justo ac dui lacinia ullamcorper."
                }
            ]
        }

    def test_expanded_path(self):
        self.assertEqual(
            utils.expand_path("./_tests/testing_sheet.csv"),
            "/home/deutschegabanna/Obsidian-Daylio-Parser/_tests/testing_sheet.csv"
        )

    def test_parsing(self):
        """Check if Entry object correctly consumes an array with data"""
        sample_row = [
            "2022-10-30",
            "October 30",
            "Sunday",
            "10:04 AM",
            "vaguely ok",
            "2ćities  skylines | dó#lóó fa$$s_ą%",
            "\"Dolomet\"",
            "\"Lorem ipsum sit dolomet amęt.\""
        ]
        sample_entry = parse_csv.Entry(sample_row)
        self.assertEqual(sample_entry.time, sample_row[3])
        self.assertEqual(sample_entry.mood, sample_row[4])
        self.assertEqual(
            sample_entry.activities,
            ["2ćities-skylines", "dólóó-fas_ą"]
        )
    
    def test_parsing_incomplete_data(self):
        """Check if Entry object correctly consumes an array with incomplete data"""
        sample_row = [
            "2022-10-30",
            "October 30",
            "Sunday",
            "10:04 AM",
            "vaguely ok"
        ]
        sample_entry = parse_csv.Entry(sample_row)
        self.assertEqual(sample_entry.time, sample_row[3])
        self.assertEqual(sample_entry.mood, sample_row[4])
        self.assertEqual(
            sample_entry.activities,
            ["2ćities-skylines", "dólóó-fas_ą"]
        )

## is this run as a main program, not component?
if __name__ == '__main__':
    unittest.main(argv=["first-arg-is-ignored"])
