import sys
import unittest
from pathlib import Path


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from HumidityDailyAudit import (  # noqa: E402
    detener_auditoria_pendiente as detener_auditoria_humedad,
)
from HumidityRules import detener_contrato_pendiente as detener_humedad  # noqa: E402


class PendingClimateRulesTest(unittest.TestCase):
    def test_humedad_sigue_bloqueada_hasta_definir_contrato(self):
        with self.assertRaisesRegex(NotImplementedError, "⚠️"):
            detener_humedad()
        with self.assertRaisesRegex(
            NotImplementedError,
            "auditoría diaria de humedad",
        ):
            detener_auditoria_humedad()


if __name__ == "__main__":
    unittest.main()
