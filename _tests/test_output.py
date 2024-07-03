import os
import shutil
import io
from unittest import TestCase

from daylio_to_md.dated_entry import DatedEntry
from daylio_to_md.dated_entries_group import DatedEntriesGroup
from daylio_to_md.librarian import Librarian
from daylio_to_md.config import options


class TestDatedEntryOutput(TestCase):
    """
    Since the sample entry can output to any stream from :class:`io.IOBase`, you can treat the StringIO as fake file
    If the contents outputted to this fake file are the same as contents written directly to another fake stream,
    then everything looks good.

    Obviously any change to formatting in the class definition will force changes in this test case.
    """

    def test_bare_minimum_entry_content(self):
        """
        Output an entry which hold information only on:

        * time
        * mood
        """
        # WHEN
        # ---
        # Create our fake entry as well as a stream that acts like a file
        options.tag_activities = True
        my_entry = DatedEntry(time="11:00", mood="great", activities="bicycle | chess")

        with io.StringIO() as my_fake_file_stream:
            my_entry.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("## great | 11:00" + "\n")
                compare_stream.write("#bicycle #chess")

                # THEN
                # ---
                # getvalue() returns the entire stream content regardless of current stream position, read() does not.
                # https://stackoverflow.com/a/53485819
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())

    def test_entry_with_title_no_note(self):
        """
        Output an entry which hold information on:

        * time
        * mood
        * title
        """
        # WHEN
        # ---
        # Create our fake entry as well as a stream that acts like a file
        options.tag_activities = True
        my_entry = DatedEntry(time="11:00", mood="great", activities="bicycle | chess", title="I'm super pumped!")

        with io.StringIO() as my_fake_file_stream:
            my_entry.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("## great | 11:00 | I'm super pumped!" + "\n")
                compare_stream.write("#bicycle #chess")

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())

    def test_entry_with_title_and_note(self):
        """
        Output an entry which hold information on:

        * time
        * mood
        * title
        * activities
        * note
        """
        # WHEN
        # ---
        # Create our fake entry as well as a stream that acts like a file
        options.tag_activities = True
        my_entry = DatedEntry(time="11:00", mood="great", activities="bicycle | chess", title="I'm super pumped!",
                              note="I believe I can fly, I believe I can touch the sky.")

        with io.StringIO() as my_fake_file_stream:
            my_entry.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("## great | 11:00 | I'm super pumped!" + "\n")
                compare_stream.write("#bicycle #chess" + "\n")
                compare_stream.write("I believe I can fly, I believe I can touch the sky.")

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())

    def test_entry_with_hashtagged_activities(self):
        """
        Output an entry which hold information on:

        * time
        * mood
        * activities (with and without hashtags)
        """
        # WHEN
        # ---
        # Create our fake entry as well as a stream that acts like a file
        options.tag_activities = True
        my_entry = DatedEntry(time="11:00", mood="great", activities="bicycle | chess")

        with io.StringIO() as my_fake_file_stream:
            my_entry.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("## great | 11:00" + "\n")
                compare_stream.write("#bicycle #chess")

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())

        # WHEN
        # ---
        # Create our fake entry as well as a stream that acts like a file
        options.tag_activities = False
        my_entry = DatedEntry(time="11:00", mood="great", activities="bicycle | chess")

        with io.StringIO() as my_fake_file_stream:
            my_entry.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("## great | 11:00" + "\n")
                compare_stream.write("bicycle chess")

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())


class TestDatedEntriesGroup(TestCase):
    def test_outputting_day_with_one_entry(self):
        """
        Creates a file-like stream for a day with one valid entry and checks if the file contents are as expected.
        """
        # WHEN
        # ---
        # Create a sample date
        sample_date = DatedEntriesGroup("2011-10-10")
        sample_date.append_to_known(DatedEntry(
            time="10:00 AM",
            mood="vaguely ok"
        ))

        with io.StringIO() as my_fake_file_stream:
            sample_date.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("---" + "\n")
                compare_stream.write("tags: daily" + "\n")
                compare_stream.write("---" + "\n"*2)

                compare_stream.write("## vaguely ok | 10:00 AM" + "\n"*2)

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())

    def test_outputting_day_with_two_entries(self):
        """
        Creates a file-like stream for a day with two valid entries and checks if the file contents are as expected.
        """
        # WHEN
        # ---
        # Create a sample date
        sample_date = DatedEntriesGroup("2011-10-10")
        sample_date.append_to_known(DatedEntry(
            time="10:00 AM",
            mood="vaguely ok",
            activities="bowling",
            note="Feeling kinda ok."
        ))
        sample_date.append_to_known(DatedEntry(
            time="9:30 PM",
            mood="awful",
            title="Everything is going downhill for me"
        ))

        with io.StringIO() as my_fake_file_stream:
            sample_date.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("---" + "\n")
                compare_stream.write("tags: daily" + "\n")
                compare_stream.write("---" + "\n"*2)

                compare_stream.write("## vaguely ok | 10:00 AM" + "\n")
                compare_stream.write("#bowling" + "\n")
                compare_stream.write("Feeling kinda ok." + "\n"*2)

                compare_stream.write("## awful | 9:30 PM | Everything is going downhill for me" + "\n"*2)

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())

    def test_outputting_day_with_two_entries_and_invalid_filetags(self):
        """
        Creates a file-like stream for a day with two valid entries and checks if the file contents are as expected.
        The tricky part is that the file tags specified by the user are invalid.
        Therefore, the entire section with filetags should be omitted in the file contents.
        """
        # WHEN
        # ---
        # Create a sample date
        sample_date = DatedEntriesGroup("2011-10-10")
        sample_date.append_to_known(DatedEntry(
            time="10:00 AM",
            mood="vaguely ok",
            activities="bowling",
            note="Feeling kinda meh."
        ))
        sample_date.append_to_known(DatedEntry(
            time="9:30 PM",
            mood="awful",
            title="Everything is going downhill for me"
        ))
        # Mess up user-configured file tags
        options.tags = ["", None]

        with io.StringIO() as my_fake_file_stream:
            sample_date.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("## vaguely ok | 10:00 AM" + "\n")
                compare_stream.write("#bowling" + "\n")
                compare_stream.write("Feeling kinda meh." + "\n"*2)

                compare_stream.write("## awful | 9:30 PM | Everything is going downhill for me" + "\n"*2)

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())

    def test_outputting_day_with_two_entries_and_partially_valid_filetags(self):
        """
        Creates a file-like stream for a day with two valid entries and checks if the file contents are as expected.
        The tricky part is that the file tags specified by the user are only partially valid.
        Therefore, the section will file tags at the beginning of the file should be sanitised.
        """
        # WHEN
        # ---
        # Create a sample date
        sample_date = DatedEntriesGroup("2011-10-10")
        sample_date.append_to_known(DatedEntry(
            time="10:00 AM",
            mood="vaguely ok",
            activities="bowling",
            note="Feeling fine, I guess."
        ))
        sample_date.append_to_known(DatedEntry(
            time="9:30 PM",
            mood="awful",
            title="Everything is going downhill for me"
        ))
        # Mess up user-configured file tags
        options.tags = ["", "foo", "bar", None]

        with io.StringIO() as my_fake_file_stream:
            sample_date.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("---" + "\n")
                compare_stream.write("tags: bar,foo" + "\n")
                compare_stream.write("---" + "\n"*2)

                compare_stream.write("## vaguely ok | 10:00 AM" + "\n")
                compare_stream.write("#bowling" + "\n")
                compare_stream.write("Feeling fine, I guess." + "\n"*2)

                compare_stream.write("## awful | 9:30 PM | Everything is going downhill for me" + "\n"*2)

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())


class TestOutputFileStructure(TestCase):
    """
    Previous test classes meant to check if each class properly handles its own output.
    This checks if the :class:`Librarian` class creates the necessary directories and outputs to files.
    """

    def test_directory_loop(self):
        """
        Loops through known dates and asks each :class:`DatedEntriesGroup` to output its contents to a specified file.
        """
        options.tags = ["daily"]

        lib = Librarian("_tests/files/journal_CSVs/sheet-1-valid-data.csv", path_to_output="_tests/files/output-results")
        lib.output_all()

        with open("_tests/files/output-results/2022/10/2022-10-25.md", encoding="UTF-8") as parsed_result:
            with open("_tests/files/expected_results/2022-10-25.md", encoding="UTF-8") as expected_result:
                self.assertListEqual(expected_result.readlines(), parsed_result.readlines())

        with open("_tests/files/output-results/2022/10/2022-10-26.md", encoding="UTF-8") as parsed_result:
            with open("_tests/files/expected_results/2022-10-26.md", encoding="UTF-8") as expected_result:
                self.assertListEqual(expected_result.readlines(), parsed_result.readlines())

        with open("_tests/files/output-results/2022/10/2022-10-27.md", encoding="UTF-8") as parsed_result:
            with open("_tests/files/expected_results/2022-10-27.md", encoding="UTF-8") as expected_result:
                self.assertListEqual(expected_result.readlines(), parsed_result.readlines())

        with open("_tests/files/output-results/2022/10/2022-10-30.md", encoding="UTF-8") as parsed_result:
            with open("_tests/files/expected_results/2022-10-30.md", encoding="UTF-8") as expected_result:
                self.assertListEqual(expected_result.readlines(), parsed_result.readlines())

    def tearDown(self) -> None:
        folder = '_tests/files/output-results'
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except OSError as e:
                print(f"Failed to delete {file_path} while cleaning up after a test. Reason: {e}")
