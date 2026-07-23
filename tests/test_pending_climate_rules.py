import json
import sys
import unittest
from pathlib import Path


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from AtmosphericPressureRules import (  # noqa: E402
    detener_contrato_pendiente as detener_presion,
)
from AtmosphericPressureDailyAudit import (  # noqa: E402
    detener_auditoria_pendiente as detener_auditoria_presion,
)
from HumidityDailyAudit import (  # noqa: E402
    detener_auditoria_pendiente as detener_auditoria_humedad,
)
from HumidityRules import detener_contrato_pendiente as detener_humedad  # noqa: E402
from WindSpeedDailyAudit import (  # noqa: E402
    detener_auditoria_pendiente as detener_auditoria_viento,
)
from WindSpeedRules import detener_contrato_pendiente as detener_viento  # noqa: E402


class PendingClimateRulesTest(unittest.TestCase):
    def test_variables_sin_contrato_fallan_de_forma_explicita(self):
        casos = (
            (detener_humedad, "Humedad"),
            (detener_presion, "Presión atmosférica"),
            (detener_viento, "Velocidad del viento"),
        )
        for detener, nombre in casos:
            with self.subTest(variable=nombre):
                with self.assertRaisesRegex(NotImplementedError, "⚠️"):
                    detener()

    def test_variables_sin_auditoria_diaria_fallan_de_forma_explicita(self):
        casos = (
            (detener_auditoria_humedad, "humedad"),
            (detener_auditoria_presion, "presión atmosférica"),
            (detener_auditoria_viento, "velocidad del viento"),
        )
        for detener, nombre in casos:
            with self.subTest(variable=nombre):
                with self.assertRaisesRegex(
                    NotImplementedError,
                    rf"auditoría diaria de {nombre}",
                ):
                    detener()

    def test_consolidador_bloquea_variables_distintas_de_precipitacion(self):
        notebook_path = PIPELINE_DIR / "05_ClimateDailyConsolidator.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        celdas = {cell.get("id"): "".join(cell["source"]) for cell in notebook["cells"]}
        config = celdas["daily_consolidation_config"].replace(
            "VARIABLE_NOMBRE = 'precipitacion'",
            "VARIABLE_NOMBRE = 'temperatura_ambiente'",
        ).replace(
            "DATASET_ID = 's54a-sgyg'",
            "DATASET_ID = 'sbwg-7ju4'",
        )
        namespace = {"__name__": "__pending_consolidation_test__"}
        exec(
            compile(
                celdas["daily_consolidation_bootstrap"],
                "daily_consolidation_bootstrap",
                "exec",
            ),
            namespace,
        )
        with self.assertRaisesRegex(NotImplementedError, "solo tiene consolidación"):
            exec(compile(config, "daily_consolidation_config", "exec"), namespace)

    def test_procesador_bloquea_humedad_sin_contrato(self):
        notebook_path = PIPELINE_DIR / "03_ClimateDailyProcessor.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        celdas = {cell.get("id"): "".join(cell["source"]) for cell in notebook["cells"]}
        config = celdas["daily_config"].replace(
            "VARIABLE_NOMBRE = 'precipitacion'",
            "VARIABLE_NOMBRE = 'humedad'",
        ).replace(
            "DATASET_ID = 's54a-sgyg'",
            "DATASET_ID = 'uext-mhny'",
        )
        namespace = {"__name__": "__pending_humidity_test__"}
        exec(compile(celdas["daily_bootstrap"], "daily_bootstrap", "exec"), namespace)
        with self.assertRaisesRegex(NotImplementedError, "Humedad"):
            exec(compile(config, "daily_config", "exec"), namespace)

    def test_auditor_bloquea_variables_sin_contrato_propio(self):
        notebook_path = PIPELINE_DIR / "04_ClimateDailyAudit.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        celdas = {cell.get("id"): "".join(cell["source"]) for cell in notebook["cells"]}
        casos = (
            ("humedad", "uext-mhny", "auditoría diaria de humedad"),
            (
                "presion_atmosferica",
                "62tk-nxj5",
                "auditoría diaria de presión atmosférica",
            ),
            (
                "velocidad_viento",
                "sgfv-3yp8",
                "auditoría diaria de velocidad del viento",
            ),
        )
        for variable, dataset_id, mensaje in casos:
            with self.subTest(variable=variable):
                config = celdas["daily_audit_config"].replace(
                    "VARIABLE_NOMBRE = 'precipitacion'",
                    f"VARIABLE_NOMBRE = '{variable}'",
                ).replace(
                    "DATASET_ID = 's54a-sgyg'",
                    f"DATASET_ID = '{dataset_id}'",
                )
                namespace = {"__name__": f"__pending_{variable}_audit_test__"}
                exec(
                    compile(
                        celdas["daily_audit_bootstrap"],
                        "daily_audit_bootstrap",
                        "exec",
                    ),
                    namespace,
                )
                with self.assertRaisesRegex(NotImplementedError, mensaje):
                    exec(compile(config, "daily_audit_config", "exec"), namespace)


if __name__ == "__main__":
    unittest.main()
