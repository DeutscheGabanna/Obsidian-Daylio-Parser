## Commits
* Use https://www.conventionalcommits.org/en/v1.0.0/ format for commit messages
* use imperative mood in commit messages (e.g. "Add feature X", "Fix bug Y", etc.)
* capitalise the type of the commit (e.g. "FEA:", "FIX:", etc.)
* ALWAYS CAPITALISE FEA:, FIX:, DOC:, etc. IN COMMIT MESSAGES

ALWAYS make sure that you use commit types that are supported by this code:
```python
COMMIT_CODES_TO_HEADINGS_MAPPING = {
    "feat": "#### ✨ New Features",
    "fix": "#### 🐛 Bug Fixes",
    "docs": "#### 📚 Documentation",
    "style": "#### 💅 Style",
    "refactor": "#### ♻️ Refactoring",
    "perf": "#### ⚡️ Performance Improvements",
    "test": "#### 🧪 Tests",
    "build": "#### 🏗️ Build System",
    "ci": "#### 🤖 CI",
    "chore": "#### 🧹 Chores",
    # Legacy mappings for backward compatibility
    "FEA": "#### ✨ New features",
    "ENH": "#### 🚀 Enhancements",
    "FIX": "#### 🐛 Fixes",
    "OPS": "#### 🔧 Operations",
    "DEP": "#### 📦 Dependencies",
    "REF": "#### ♻️ Refactoring",
    "TST": "#### 🧪 Testing",
    "MRG": "#### 🔀 Other",
    "REV": "#### ⏮️ Reversions",
    "CHO": "#### 🧹 Chores",
    "STY": "#### 💅 Style",
    "WIP": "#### 🚧 Other",
    "DOC": "#### 📚 Other",
}
```
do not use DOCS, use DOC! if you need this commit type. I'd rather use the legacy versions capitalised than the new ones in lowercase, to be honest. The new ones are more intuitive but the legacy ones are more widely used and recognised, so I think it's better to stick with them for now.
This let's us generate automatic PR descriptions and changelogs based on the commit messages, which is a great way to keep track of the changes in the project and to communicate them to the users.