"""Creates an .MD file based on the string provided by compile_md.py"""
import hashlib
import os
# Custom
from cmd_args import settings

class Note:
    """Note is a file encompassing every entry made on a given date"""
    def __init__(self, day, contents):
        self.day = day
        self.contents = contents
        self.path = f"{os.path.join(settings.destination, settings.prefix)}{day}{settings.suffix}.md"
        self.control_sum = hashlib.sha256()
        temp_contents = self.contents # we need a temporary contents var to be consumed
        for byte_block in iter(lambda: temp_contents[:4096].encode('utf-8'), b""):
            self.control_sum.update(byte_block)
            temp_contents = temp_contents[4096:]

    def create_file(self):
        """Tries to create or overwrite file from self.path with self.contents
        Raises PermissionError if file exists and user does not want it overwritten."""
        if os.path.exists(self.path) and self.compare_existing() is True:
            # User can have note files from previous runs of the script
            choice = None # [None, yes, no]
            # TODO: support for forcing overwrites if optional argument is set to True
            while choice is None:
                answer = input(f"{self.path} already exists and differs. Overwrite? (y/n) ")
                if str(answer).lower() in ["yes", "y"]:
                    choice = True
                    self.output_contents()
                elif str(answer).lower() in ["no", "n"]:
                    choice = False
            if choice is False:
                raise PermissionError("User denied overwrite")
        else:
            self.output_contents()

    def output_contents(self):
        """Opens self.path and outputs self.contents.
        Recurring usage in self.create_file()"""
        with open(self.path, 'w', encoding='UTF-8') as file:
            file.write(self.contents)

    def compare_existing(self):
        """Calculates checksum for file existing at self.path.
        Returns True if matches self.contents."""
        control_sum_existing_file = hashlib.sha256()
        with open(self.path,"rb") as f:
            for byte_block in iter(lambda: f.read(4096),b""):
                control_sum_existing_file.update(byte_block)
        return control_sum_existing_file.hexdigest() == self.control_sum.hexdigest()
