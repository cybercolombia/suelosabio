import ast
import json
import sys
import unittest
from pathlib import Path

import pandas as pd


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from TemperatureDailyAudit import (  # noqa: E402
    auditar_temperatura_diaria,
    validar_capa_diaria,
)


def fila_diaria(sensor, fecha, media, minima, maxima, cobertura=100.0):
    return {
        "variable": "temperatura_ambiente",
        "dataset_id": "sbwg-7ju4",
        "departamento": "CUNDINAMARCA",
        "codigoestacion": "E1",
        "codigosensor": sensor,
        "fecha": fecha,
        "temperatura_principal_observada_c": media,
        "temperatura_media_observada_c": media,
        "temperatura_mediana_observada_c": media,
        "temperatura_minima_observada_c": minima,
        "temperatura_maxima_observada_c": maxima,
        "amplitud_termica_observada_c": maxima - minima,
        "observaciones_validas": 24,
        "municipios_observados": "TEST",
        "nombres_estacion_observados": "ESTACION TEST",
        "intervalo_moda_segundos": 3600.0,
        "observaciones_esperadas": 24.0,
        "cobertura_observada_pct": cobertura,
        "cobertura_evaluable": True,
        "temperatura_diaria_c": pd.NA,
        "calidad_dia": "PENDIENTE_REGLA_COBERTURA",
        "regla_version": "temperatura_diaria_v1",
        "conflictos_excluidos": 0,
    }


class TemperatureDailyAuditTest(unittest.TestCase):
    def setUp(self):
        self.diario = pd.DataFrame(
            [
                fila_diaria("0068", "2025-01-01", 15.0, 10.0, 20.0),
                fila_diaria("0068", "2025-01-03", 20.0, -12.0, 47.0),
                fila_diaria("0071", "2025-01-01", 15.5, 10.0, 21.0),
                fila_diaria("0071", "2025-01-03", 22.0, 18.0, 25.0, 101.0),
            ]
        )

    def test_construye_calendario_sin_imputar_temperatura(self):
        resultado = auditar_temperatura_diaria(self.diario)

        self.assertEqual(len(resultado.calendario), 62)
        self.assertEqual(resultado.calendario["es_dia_ausente"].sum(), 58)
        ausentes = resultado.calendario.loc[resultado.calendario["es_dia_ausente"]]
        self.assertTrue(ausentes["temperatura_principal_observada_c"].isna().all())

    def test_detecta_extremos_amplitud_y_cobertura(self):
        resultado = auditar_temperatura_diaria(self.diario)
        motivos = "|".join(resultado.valores_sospechosos["motivos_revision"])

        self.assertIn("TEMPERATURA_MUY_BAJA", motivos)
        self.assertIn("TEMPERATURA_MUY_ALTA", motivos)
        self.assertIn("AMPLITUD_DIARIA_MUY_ALTA", motivos)
        self.assertIn("COBERTURA_MAYOR_100", motivos)

    def test_compara_sensores_en_celsius_sin_promediarlos(self):
        resultado = auditar_temperatura_diaria(self.diario)
        resumen = resultado.resumen_sensores_paralelos.iloc[0]

        self.assertEqual(len(resultado.resumen_sensores_paralelos), 1)
        self.assertEqual(resumen["dias_ambos_observados"], 2)
        self.assertEqual(resumen["dias_concuerdan_tolerancia"], 1)
        self.assertAlmostEqual(resumen["diferencia_abs_max_c"], 2.0)

    def test_rechaza_estadisticos_incoherentes(self):
        incoherente = self.diario.iloc[[0]].copy()
        incoherente["temperatura_minima_observada_c"] = 30.0

        with self.assertRaisesRegex(ValueError, "incoherentes"):
            validar_capa_diaria(incoherente)


class TemperatureDailyAuditNotebookTest(unittest.TestCase):
    def test_run_all_temperatura_permanece_protegido(self):
        notebook_path = PIPELINE_DIR / "03_01_ClimateDailyAudit.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        namespace = {"__name__": "__temperature_daily_audit_notebook_test__"}

        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            source = source.replace(
                "VARIABLE_NOMBRE = 'precipitacion'",
                "VARIABLE_NOMBRE = 'temperatura_ambiente'",
            ).replace(
                "DATASET_ID = 's54a-sgyg'",
                "DATASET_ID = 'sbwg-7ju4'",
            )
            ast.parse(source, filename=f"cell_{index}")
            exec(compile(source, f"cell_{index}", "exec"), namespace)

        self.assertFalse(namespace["EJECUTAR_AUDITORIA_DIARIA"])
        self.assertIsNone(namespace["resultado_auditoria"])
        self.assertEqual(namespace["AUDIT_VERSION"], "auditoria_temperatura_diaria_v1")
        self.assertIn("temperatura_ambiente", namespace["NOMBRES_SALIDA"]["reporte"])

        diario = pd.DataFrame(
            [fila_diaria("0068", "2025-01-01", 15.0, 10.0, 20.0)]
        )
        resultado = namespace["AUDITAR_VARIABLE"](diario)
        momento = pd.Timestamp.now(tz="America/Bogota").to_pydatetime()
        reporte = namespace["construir_reporte"](
            resultado,
            [],
            momento,
            momento,
            0.0,
        )
        self.assertIn("Auditoría diaria de temperatura_ambiente", reporte)
        self.assertIn("temperatura_principal_observada_c", reporte)


if __name__ == "__main__":
    unittest.main()
