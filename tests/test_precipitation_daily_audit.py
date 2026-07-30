import ast
import json
import sys
import unittest
from pathlib import Path

import pandas as pd


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from PrecipitationDailyAudit import (  # noqa: E402
    auditar_precipitacion_diaria,
    validar_capa_diaria,
)


def fila_diaria(sensor, fecha, precipitacion, cobertura=100.0, positivas=1):
    return {
        "variable": "precipitacion",
        "dataset_id": "s54a-sgyg",
        "departamento": "CUNDINAMARCA",
        "codigoestacion": "E1",
        "codigosensor": sensor,
        "fecha": fecha,
        "precipitacion_observada_mm": precipitacion,
        "observaciones_validas": 144,
        "observaciones_positivas": positivas,
        "valor_intervalo_max_mm": precipitacion if positivas else 0.0,
        "municipios_observados": "TEST",
        "nombres_estacion_observados": "ESTACION TEST",
        "intervalo_moda_segundos": 600.0,
        "observaciones_esperadas": 144.0,
        "cobertura_observada_pct": cobertura,
        "cobertura_evaluable": True,
        "precipitacion_diaria_mm": pd.NA,
        "calidad_dia": "PENDIENTE_REGLA_COBERTURA",
        "regla_version": "precipitacion_incremental_v1",
    }


class PrecipitationDailyAuditTest(unittest.TestCase):
    def setUp(self):
        self.diario = pd.DataFrame(
            [
                fila_diaria("0240", "2025-01-01", 0.0, positivas=0),
                fila_diaria("0240", "2025-01-03", 500.0, positivas=144),
                fila_diaria("0257", "2025-01-01", 0.0, positivas=0),
                fila_diaria("0257", "2025-01-03", 10.0, cobertura=101.0),
            ]
        )

    def test_construye_calendario_sin_convertir_ausencia_en_cero(self):
        resultado = auditar_precipitacion_diaria(self.diario)

        self.assertEqual(len(resultado.calendario), 62)
        self.assertEqual(resultado.calendario["es_dia_ausente"].sum(), 58)
        ausentes = resultado.calendario.loc[resultado.calendario["es_dia_ausente"]]
        self.assertTrue(ausentes["precipitacion_observada_mm"].isna().all())
        resumen = resultado.resumen_particiones.iloc[0]
        self.assertEqual(resumen["dias_con_algun_registro"], 2)
        self.assertEqual(resumen["dias_sin_ningun_registro"], 29)
        par = resultado.resumen_pares.iloc[0]
        self.assertEqual(par["primera_fecha_observada"], pd.Timestamp("2025-01-01"))
        self.assertEqual(par["ultima_fecha_observada"], pd.Timestamp("2025-01-03"))

    def test_detecta_extremos_y_cobertura_superior_a_cien(self):
        resultado = auditar_precipitacion_diaria(self.diario)
        motivos = "|".join(resultado.valores_sospechosos["motivos_revision"])

        self.assertIn("TOTAL_DIARIO_MUY_ALTO", motivos)
        self.assertIn("POSITIVOS_PERSISTENTES", motivos)
        self.assertIn("COBERTURA_MAYOR_100", motivos)
        self.assertTrue(
            resultado.calendario["estado_cobertura_candidato"]
            .eq("MAYOR_100_REVISAR")
            .any()
        )

    def test_compara_sensores_sin_sumarlos(self):
        resultado = auditar_precipitacion_diaria(self.diario)
        resumen = resultado.resumen_sensores_paralelos.iloc[0]

        self.assertEqual(len(resultado.resumen_sensores_paralelos), 1)
        self.assertEqual(resumen["dias_ambos_observados"], 2)
        self.assertEqual(resumen["dias_concuerdan_tolerancia"], 1)
        self.assertAlmostEqual(resumen["diferencia_abs_max_mm"], 490.0)

    def test_rechaza_llaves_diarias_duplicadas(self):
        duplicado = pd.concat([self.diario, self.diario.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "llaves.*repetidas"):
            validar_capa_diaria(duplicado)

    def test_conserva_esquema_si_no_hay_sensores_paralelos(self):
        resultado = auditar_precipitacion_diaria(
            self.diario.loc[self.diario["codigosensor"].eq("0240")]
        )

        self.assertTrue(resultado.comparaciones_sensores.empty)
        self.assertIn("diferencia_abs_mm", resultado.comparaciones_sensores.columns)
        self.assertTrue(resultado.resumen_sensores_paralelos.empty)

    def test_detecta_mes_completo_ausente_dentro_del_periodo_activo(self):
        diario = pd.DataFrame(
            [
                fila_diaria("0240", "2024-01-15", 1.0),
                fila_diaria("0240", "2024-03-15", 2.0),
                {
                    **fila_diaria("0240", "2024-02-10", 3.0),
                    "codigoestacion": "E2",
                },
            ]
        )

        resultado = auditar_precipitacion_diaria(diario)

        ausencia = resultado.ausencias_mes_completo
        self.assertEqual(len(ausencia), 1)
        self.assertEqual(ausencia.iloc[0]["codigoestacion"], "E1")
        self.assertEqual(ausencia.iloc[0]["periodo"], "2024-02")
        febrero_e1 = resultado.calendario.loc[
            resultado.calendario["codigoestacion"].eq("E1")
            & resultado.calendario["anio"].eq(2024)
            & resultado.calendario["mes"].eq(2)
        ]
        self.assertEqual(len(febrero_e1), 29)
        self.assertTrue(febrero_e1["es_dia_ausente"].all())
        self.assertTrue(febrero_e1["precipitacion_observada_mm"].isna().all())

    def test_no_exige_meses_anteriores_al_alta_ni_posteriores_a_la_baja(self):
        diario = pd.DataFrame(
            [
                fila_diaria("0240", "2024-01-15", 1.0),
                fila_diaria("0240", "2024-03-15", 2.0),
                {
                    **fila_diaria("0240", "2024-02-10", 3.0),
                    "codigoestacion": "E2",
                },
            ]
        )

        resultado = auditar_precipitacion_diaria(diario)
        actividad_e2 = resultado.actividad_mensual.loc[
            resultado.actividad_mensual["codigoestacion"].eq("E2")
        ]

        self.assertEqual(actividad_e2["periodo"].tolist(), ["2024-02"])
        self.assertTrue(actividad_e2["mes_observado"].all())


class ClimateDailyAuditNotebookTest(unittest.TestCase):
    def test_run_all_permanece_protegido(self):
        notebook_path = (
            PIPELINE_DIR / "04_Climate_Precipitation_DailyAudit.ipynb"
        )
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        namespace = {"__name__": "__daily_audit_notebook_test__"}

        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            ast.parse(source, filename=f"cell_{index}")
            exec(compile(source, f"cell_{index}", "exec"), namespace)

        self.assertFalse(namespace["EJECUTAR_AUDITORIA_DIARIA"])
        self.assertFalse(namespace["EJECUTAR_GRAFICA_INTERACTIVA"])
        self.assertFalse(namespace["GRAFICA_USAR_RESULTADO_EN_MEMORIA"])
        self.assertIsNone(namespace["resultado_auditoria"])
        self.assertEqual(
            namespace["AUDIT_VERSION"], "auditoria_precipitacion_diaria_v2"
        )
        self.assertEqual(
            namespace["NOMBRES_SALIDA"]["ausencias_mes"],
            "ausencias_mes_completo.parquet",
        )


if __name__ == "__main__":
    unittest.main()
