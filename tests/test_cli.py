"""End-to-end test: invoke the CLI as a subprocess and compare gold files."""
import subprocess
import sys
from pathlib import Path


def _tree(path: Path) -> str:
    if not path.exists():
        return f"  {path} [does not exist]"
    lines = [f"  {item.relative_to(path)}{'/' if item.is_dir() else ''}"
             for item in sorted(path.rglob("*"))]
    return "\n".join(lines) if lines else "  [empty]"


class TestCli:
    def test_generates_expected_markdown(self, ok_csv, ok_expected_dir, tmp_path):
        completed = subprocess.run(
            [sys.executable, "-m", "obsidian_daylio_parser", str(ok_csv), str(tmp_path)],
            capture_output=True, text=True, check=False
        )
        assert completed.returncode == 0, (
            f"CLI exited {completed.returncode}.\nstderr:\n{completed.stderr}\ntree:\n{_tree(tmp_path)}"
        )

        generated = {p.name: p for p in sorted(tmp_path.rglob("*.md"))}
        expected = {p.name: p for p in sorted(ok_expected_dir.glob("*.md"))}

        assert set(expected) == set(generated), (
            f"missing: {sorted(set(expected) - set(generated))}\n"
            f"extra:   {sorted(set(generated) - set(expected))}"
        )

        for name, expected_path in sorted(expected.items()):
            assert expected_path.read_text("UTF-8") == generated[name].read_text("UTF-8"), (
                f"Content mismatch for {name}"
            )
