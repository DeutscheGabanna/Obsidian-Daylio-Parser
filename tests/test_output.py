import io
import os
import shutil
from unittest import TestCase

from daylio_to_md.group import EntriesFrom, EntriesFromBuilder
from daylio_to_md.journal_entry import Entry, EntryBuilder
from daylio_to_md.librarian import Librarian


class TestEntriesFromOutput(TestCase):
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
        my_entry = Entry(time="11:00", mood="great", activities="bicycle | chess")

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
        my_entry = Entry(time="11:00", mood="great", activities="bicycle | chess", title="I'm super pumped!")

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
        my_entry = Entry(time="11:00", mood="great", activities="bicycle | chess", title="I'm super pumped!",
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
        my_entry = Entry(time="11:00", mood="great", activities="bicycle | chess")

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
        my_entry = Entry(time="11:00", mood="great", activities="bicycle | chess", tag_activities=False)

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

    def test_header_multiplier(self):
        # WHEN
        # ---
        # Create our fake entry as well as a stream that acts like a file
        my_entry = Entry(time="11:00", mood="great", title="Feeling pumped@!", header_multiplier=5)

        with io.StringIO() as my_fake_file_stream:
            my_entry.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("##### great | 11:00 | Feeling pumped@!")

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())


class TestDatedEntriesGroup(TestCase):
    def setUp(self):
        # It's okay to store information on created instances in a single run for a normal user, not for repeated tests
        # Therefore we reset the memory of the class before every test
        EntriesFrom._instances = {}

    def test_outputting_day_with_one_entry(self):
        """
        Creates a file-like stream for a day with one valid entry and checks if the file contents are as expected.
        """
        # WHEN
        # ---
        # Create a sample date
        sample_date = EntriesFrom("2011-10-10")
        entry_one = Entry(
            time="10:00 AM",
            mood="vaguely ok"
        )
        sample_date.add(entry_one)

        with io.StringIO() as my_fake_file_stream:
            sample_date.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("---" + "\n")
                compare_stream.write("tags: daylio" + "\n")
                compare_stream.write("---" + "\n" * 2)

                compare_stream.write("## vaguely ok | 10:00" + "\n" * 2)

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
        sample_date = EntriesFrom("2011-10-10")
        entry_one = Entry(
            time="10:00 AM",
            mood="vaguely ok",
            activities="bowling",
            note="Feeling kinda ok."
        )
        entry_two = Entry(
            time="9:30 PM",
            mood="awful",
            title="Everything is going downhill for me"
        )
        sample_date.add(entry_one, entry_two)

        with io.StringIO() as my_fake_file_stream:
            sample_date.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("---" + "\n")
                compare_stream.write("tags: daylio" + "\n")
                compare_stream.write("---" + "\n" * 2)

                compare_stream.write("## vaguely ok | 10:00" + "\n")
                compare_stream.write("#bowling" + "\n")
                compare_stream.write("Feeling kinda ok." + "\n" * 2)

                compare_stream.write("## awful | 21:30 | Everything is going downhill for me" + "\n" * 2)

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())

    def test_outputting_day_with_two_entries_and_invalid_filetags(self):
        """
        Creates a file-like stream for a day with two valid entries and checks if the file contents are as expected.
        The tricky part is that the file frontmatter_tags specified by the user are invalid.
        Therefore, the entire section with filetags should be omitted in the file contents.
        """
        # WHEN
        # ---
        # Create a sample date
        sample_date = EntriesFrom("2011-10-10", front_matter_tags=["", None])
        entry_one = Entry(
            time="10:00 AM",
            mood="vaguely ok",
            activities="bowling",
            note="Feeling kinda meh."
        )
        entry_two = Entry(
            time="9:30 PM",
            mood="awful",
            title="Everything is going downhill for me"
        )
        sample_date.add(entry_one, entry_two)

        with io.StringIO() as my_fake_file_stream:
            sample_date.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("## vaguely ok | 10:00" + "\n")
                compare_stream.write("#bowling" + "\n")
                compare_stream.write("Feeling kinda meh." + "\n" * 2)

                compare_stream.write("## awful | 21:30 | Everything is going downhill for me" + "\n" * 2)

                # THEN
                # ---
                self.assertEqual(compare_stream.getvalue(), my_fake_file_stream.getvalue())

    def test_outputting_day_with_two_entries_and_partially_valid_filetags(self):
        """
        Creates a file-like stream for a day with two valid entries and checks if the file contents are as expected.
        The tricky part is that the file frontmatter_tags specified by the user are only partially valid.
        Therefore, the section will file frontmatter_tags at the beginning of the file should be sanitised.
        """
        # WHEN
        # ---
        # Create a sample date
        sample_date = EntriesFrom("2011-10-10", front_matter_tags=["", "foo", "bar", None])
        entry_one = Entry(
            time="10:00 AM",
            mood="vaguely ok",
            activities="bowling",
            note="Feeling fine, I guess."
        )
        entry_two = Entry(
            time="9:30 PM",
            mood="awful",
            title="Everything is going downhill for me"
        )
        sample_date.add(entry_one, entry_two)

        with io.StringIO() as my_fake_file_stream:
            sample_date.output(my_fake_file_stream)
            # AND
            # ---
            # Then create another stream and fill it with the same content, but written directly, not through object
            with io.StringIO() as compare_stream:
                compare_stream.write("---" + "\n")
                compare_stream.write("tags: bar,foo" + "\n")
                compare_stream.write("---" + "\n" * 2)

                compare_stream.write("## vaguely ok | 10:00" + "\n")
                compare_stream.write("#bowling" + "\n")
                compare_stream.write("Feeling fine, I guess." + "\n" * 2)

                compare_stream.write("## awful | 21:30 | Everything is going downhill for me" + "\n" * 2)

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
        Loops through known dates and asks each :class:`EntriesFrom` to output its contents to a specified file.
        """

        lib = Librarian("tests/files/all-valid.csv", path_to_output="tests/files/scenarios/ok/out")
        lib.output_all()

        with open("tests/files/scenarios/ok/out/2022/10/2022-10-25.md", encoding="UTF-8") as parsed_result, \
                open("tests/files/scenarios/ok/expect/2022-10-25.md", encoding="UTF-8") as expected_result:
            self.assertListEqual(expected_result.readlines(), parsed_result.readlines())

        with open("tests/files/scenarios/ok/out/2022/10/2022-10-26.md", encoding="UTF-8") as parsed_result, \
                open("tests/files/scenarios/ok/expect/2022-10-26.md", encoding="UTF-8") as expected_result:
            self.assertListEqual(expected_result.readlines(), parsed_result.readlines())

        with open("tests/files/scenarios/ok/out/2022/10/2022-10-27.md", encoding="UTF-8") as parsed_result, \
                open("tests/files/scenarios/ok/expect/2022-10-27.md", encoding="UTF-8") as expected_result:
            self.assertListEqual(expected_result.readlines(), parsed_result.readlines())

        with open("tests/files/scenarios/ok/out/2022/10/2022-10-30.md", encoding="UTF-8") as parsed_result, \
                open("tests/files/scenarios/ok/expect/2022-10-30.md", encoding="UTF-8") as expected_result:
            self.assertListEqual(expected_result.readlines(), parsed_result.readlines())

    def tearDown(self) -> None:
        folder = 'tests/files/scenarios/ok/out'
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except OSError as e:
                print(f"Failed to delete {file_path} while cleaning up after a test. Reason: {e}")
