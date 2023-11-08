# Obsidian Daylio to Markdown Parser
Daylio is an amazing journaling and mood-tracking app, but you may want to store your journals also in an Obsidian Vault. For that you need a "translator" (or a parser, more technically speaking) that knows how to transfer Daylio entries into Obsidian notes.

![Daylio to Obsidian](https://user-images.githubusercontent.com/59067099/198896455-41bb9496-7efc-4102-b311-f1db614a2d96.png)

## Installation
1. Clone the repo.
```
git clone https://github.com/DeutscheGabanna/Obsidian-Daylio-Parser.git
```
2. Change your working directory to the downloaded repo folder.
```
cd Obsidian-Daylio-Parser
```
3. Run main.py. First argument should point to the .CSV file you want to parse, and the second one - to the directory where you want to output .MD notes.
```
python main.py input_file.csv output_dir
```
If in doubt, there's always `python main.py --help`. Follow the instructions included there. Basically it lists all the options available for you.
