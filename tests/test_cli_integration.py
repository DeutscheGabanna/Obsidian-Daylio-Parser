import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase


class TestCliIntegration(TestCase):
    def test_cli_generates_expected_markdown_files(self):
        repo_root = Path(__file__).resolve().parent.parent
        input_csv = repo_root / "tests" / "files" / "scenarios" / "ok" / "all-valid.csv"
        expected_dir = repo_root / "tests" / "files" / "scenarios" / "ok" / "expect"

        with tempfile.TemporaryDirectory(prefix="daylio-integration-") as tmp_dir:
            output_dir = Path(tmp_dir)
            completed = subprocess.run(
                ["daylio_to_md", str(input_csv), str(output_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                0,
                completed.returncode,
                msg=f"CLI failed. stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
            )

            expected_files = sorted(expected_dir.glob("*.md"))
            generated_files = sorted((output_dir / "2022" / "10").glob("*.md"))

            self.assertListEqual(
                [path.name for path in expected_files],
                [path.name for path in generated_files],
                msg="Generated file list does not match expected fixtures.",
            )

            for expected in expected_files:
                generated = output_dir / "2022" / "10" / expected.name
                self.assertTrue(generated.exists(), msg=f"Missing expected output file: {generated}")
                self.assertEqual(
                    expected.read_text(encoding="UTF-8"),
                    generated.read_text(encoding="UTF-8"),
                    msg=f"Content mismatch for {expected.name}",
                )

