import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.notebook_outputs import (
    clear_execution_state,
    execution_state,
    process_notebooks,
)


def notebook_with_output() -> dict:
    return {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "outputs": [{"name": "stdout", "output_type": "stream", "text": ["ok\n"]}],
                "source": ["print('ok')"],
            }
        ],
        "metadata": {"widgets": {"application/vnd.jupyter.widget-state+json": {}}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


class NotebookOutputsTest(unittest.TestCase):
    def test_detects_and_clears_execution_state(self):
        notebook = notebook_with_output()

        self.assertEqual(
            execution_state(notebook),
            ["celda 1: outputs", "celda 1: execution_count", "metadata: widgets"],
        )
        self.assertTrue(clear_execution_state(notebook))
        self.assertEqual(execution_state(notebook), [])

    def test_fix_persists_clean_notebook(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "example.ipynb"
            path.write_text(json.dumps(notebook_with_output()), encoding="utf-8")

            reviewed, affected, errors = process_notebooks([path], fix=True)
            persisted = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual((reviewed, affected, errors), (1, 1, 0))
        self.assertEqual(execution_state(persisted), [])


if __name__ == "__main__":
    unittest.main()
