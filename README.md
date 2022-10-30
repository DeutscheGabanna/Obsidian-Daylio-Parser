# Obsidian Daylio to Markdown Parser
Daylio is an amazing journaling and mood-tracking app, but you may want to store your journals also in an Obsidian Vault. For that you need a "translator" (or a parser, more technically speaking) that knows how to transfer Daylio entries into Obsidian notes.

![Daylio to Obsidian](https://user-images.githubusercontent.com/59067099/198896455-41bb9496-7efc-4102-b311-f1db614a2d96.png)

## How-to
Knowledge on how to run Python scripts is at the moment necessary to run this thing. I do not have time now to explain it, but I may streamline this or make a manual in the future.

**Important**:
- the folder from which you run this script is the default folder for all the new notes. Since you might have thousands of Daylio entries, be advised not to run the script on your Desktop or Downloads folder, because it will get messy.
- the Daylio export file has to be named **daylio.csv**. I'm sorry you have to rename your file or the code, I might add more flexibility to this later.
- the Daylio export file has to be in the same directory as the Python script.
- you can tweak some parameters in the code to adjust it to your preferences. The parameters are at the top of the file.
- running the script again overwrites the old .md notes. If you have any files in that folder that match "YYYY-MM-DD.md" template, you'd better run the script somewhere else.
