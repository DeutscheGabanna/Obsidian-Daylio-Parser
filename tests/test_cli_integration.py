import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase


class TestCliIntegration(TestCase):
    maxDiff = None

    @staticmethod
    def _tree(path: Path) -> str:
        """Return a recursive listing of path, or a notice if it doesn't exist."""
        if not path.exists():
            return f"  {path} [does not exist]"
        lines = []
        for item in sorted(path.rglob("*")):
            rel = item.relative_to(path)
            suffix = "/" if item.is_dir() else ""
            lines.append(f"  {rel}{suffix}")
        return "\n".join(lines) if lines else "  [empty]"

    def test_cli_generates_expected_markdown_files(self):
        repo_root = Path(__file__).resolve().parent.parent
        input_csv = repo_root / "tests" / "files" / "scenarios" / "ok" / "all-valid.csv"
        expected_dir = repo_root / "tests" / "files" / "scenarios" / "ok" / "expect"

        with tempfile.TemporaryDirectory(prefix="daylio-integration-") as tmp_dir:
            output_dir = Path(tmp_dir)

            # --- Run CLI ---
            completed = subprocess.run(
                ["daylio_to_md", str(input_csv), str(output_dir)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                0,
                completed.returncode,
                msg=(
                    f"CLI exited with code {completed.returncode}.\n"
                    f"stdout:\n{completed.stdout}\n"
                    f"stderr:\n{completed.stderr}\n"
                    f"output tree:\n{self._tree(output_dir)}"
                ),
            )

            # --- Discover files ---
            # Don't hardcode year/month — find all .md files the CLI actually wrote.
            generated_by_name = {p.name: p for p in sorted(output_dir.rglob("*.md"))}
            expected_by_name = {p.name: p for p in sorted(expected_dir.glob("*.md"))}

            tree = self._tree(output_dir)

            # --- Compare file sets ---
            self.assertSetEqual(
                set(expected_by_name.keys()),
                set(generated_by_name.keys()),
                msg=(
                    f"missing: {sorted(set(expected_by_name) - set(generated_by_name))}\n"
                    f"extra:   {sorted(set(generated_by_name) - set(expected_by_name))}\n"
                    f"output tree:\n{tree}\n"
                    f"stderr:\n{completed.stderr}"
                ),
            )

            # --- Compare each file independently ---
            for name, expected_path in sorted(expected_by_name.items()):
                with self.subTest(file=name):
                    generated_path = generated_by_name.get(name)
                    self.assertIsNotNone(
                        generated_path,
                        msg=f"{name} missing from output.\noutput tree:\n{tree}",
                    )
                    self.assertMultiLineEqual(
                        expected_path.read_text(encoding="UTF-8"),
                        generated_path.read_text(encoding="UTF-8"),
                        msg=f"Content mismatch for {name}",
                    )
