"""Contains universally useful functions"""
import re
import os
import logging

def slugify(text, taggify):
    """Simple slugification function"""
    text = str(text).lower()
    text = re.sub(re.compile(r"\s+"), '-', text)      # Replace spaces with -
    text = re.sub(re.compile(r"[^\w\-]+"), '', text)   # Remove all non-word chars
    text = re.sub(re.compile(r"\-\-+"), '-', text)    # Replace multiple - with single -
    text = re.sub(re.compile(r"^-+"), '', text)       # Trim - from start of text
    text = re.sub(re.compile(r"-+$"), '', text)       # Trim - from end of text
    if taggify:
        if re.match('[0-9]', text):
            logging.warning("You want your activities as tags, but %s is invalid.", text)
    return text

def expand_path(path):
    """Expand all %variables%, ~/home-directories and relative parts in the path
    Return the expanded, absolute path"""
    # Expands the tilde (~) character to the user's home directory
    return os.path.expanduser(
        # Expands environment variables in the path, such as %appdata%
        os.path.expandvars(
            # Converts the filepath to an absolute path
            os.path.abspath(path)
        )
    )
