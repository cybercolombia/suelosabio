import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = REPO_ROOT / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from DatasetConfig import (  # noqa: E402
    COLAB_PROCESSED_ROOT,
    LOCAL_PROCESSED_ROOT,
    cargar_configuracion_datasets,
)


class DatasetConfigTest(unittest.TestCase):
    def test_configuracion_local_usa_google_drive_sin_montar(self):
        montajes = []
        config = cargar_configuracion_datasets(
            in_colab=False,
            drive_mounter=lambda: montajes.append(True),
        )

        self.assertFalse(config.in_colab)
        self.assertEqual(config.processed_root, LOCAL_PROCESSED_ROOT)
        self.assertEqual(config.eva_raw_root, LOCAL_PROCESSED_ROOT / "eva_cruda")
        self.assertEqual(montajes, [])

    def test_configuracion_colab_monta_drive(self):
        montajes = []
        config = cargar_configuracion_datasets(
            in_colab=True,
            drive_mounter=lambda: montajes.append(True),
        )

        self.assertTrue(config.in_colab)
        self.assertEqual(config.processed_root, COLAB_PROCESSED_ROOT)
        self.assertEqual(montajes, [True])

    def test_variables_de_entorno_sobrescriben_rutas(self):
        with patch.dict(
            os.environ,
            {
                "SUELOSABIO_SHARED_ROOT": "/tmp/shared-test",
                "SUELOSABIO_PROCESSED_ROOT": "/tmp/processed-test",
            },
        ):
            config = cargar_configuracion_datasets(
                in_colab=False,
                montar_drive=False,
            )

        self.assertEqual(config.shared_root, Path("/tmp/shared-test"))
        self.assertEqual(config.processed_root, Path("/tmp/processed-test"))


if __name__ == "__main__":
    unittest.main()
