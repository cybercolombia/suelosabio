import ast
import json
import sys
import unittest
from pathlib import Path

import pandas as pd


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from PrecipitationDailyConsolidation import (  # noqa: E402
    consolidar_precipitacion_diaria,
)


def fila_calendario(
    sensor,
    fecha,
    precipitacion,
    *,
    cobertura=100.0,
    observado=True,
    estacion="E1",
):
    return {
        "variable": "precipitacion",
        "dataset_id": "s54a-sgyg",
        "departamento": "CUNDINAMARCA",
        "codigoestacion": estacion,
        "codigosensor": sensor,
        "fecha": fecha,
        "es_dia_observado": observado,
        "precipitacion_observada_mm": precipitacion if observado else pd.NA,
        "cobertura_observada_pct": cobertura if observado else pd.NA,
        "cobertura_evaluable": observado,
        "municipios_observados": "TEST" if observado else pd.NA,
        "nombres_estacion_observados": "ESTACION TEST" if observado else pd.NA,
        "latitud_mediana": 4.5 if observado else pd.NA,
        "longitud_mediana": -74.1 if observado else pd.NA,
    }


def fila_sospechosa(sensor, fecha, motivo, estacion="E1"):
    return {
        "departamento": "CUNDINAMARCA",
        "codigoestacion": estacion,
        "codigosensor": sensor,
        "fecha": fecha,
        "motivos_revision": motivo,
    }


class PrecipitationDailyConsolidationTest(unittest.TestCase):
    def test_ausencia_permanece_nan(self):
        calendario = pd.DataFrame(
            [fila_calendario("0240", "2025-01-01", None, observado=False)]
        )
        resultado = consolidar_precipitacion_diaria(calendario, pd.DataFrame())
        fila = resultado.diario_estacion.iloc[0]

        self.assertTrue(fila["es_dia_faltante"])
        self.assertTrue(pd.isna(fila["precipitacion_diaria_mm"]))
        self.assertEqual(fila["calidad_dia"], "SIN_OBSERVACION")

    def test_aplica_ventana_de_cobertura(self):
        calendario = pd.DataFrame(
            [
                fila_calendario("0240", "2025-01-01", 2.0, cobertura=89.0),
                fila_calendario("0240", "2025-01-02", 3.0, cobertura=101.5),
                fila_calendario("0240", "2025-01-03", 4.0, cobertura=103.0),
            ]
        )
        resultado = consolidar_precipitacion_diaria(calendario, pd.DataFrame())
        diario = resultado.diario_estacion.set_index("fecha")

        self.assertTrue(pd.isna(diario.loc[pd.Timestamp("2025-01-01"), "precipitacion_diaria_mm"]))
        self.assertEqual(diario.loc[pd.Timestamp("2025-01-02"), "precipitacion_diaria_mm"], 3.0)
        self.assertTrue(pd.isna(diario.loc[pd.Timestamp("2025-01-03"), "precipitacion_diaria_mm"]))

    def test_cuarentena_patron_persistente(self):
        calendario = pd.DataFrame(
            [
                fila_calendario("0240", f"2025-01-0{dia}", 500.0)
                for dia in range(1, 5)
            ]
        )
        sospechosos = pd.DataFrame(
            [
                fila_sospechosa(
                    "0240",
                    f"2025-01-0{dia}",
                    "TOTAL_DIARIO_MUY_ALTO|POSITIVOS_PERSISTENTES",
                )
                for dia in range(1, 4)
            ]
        )
        resultado = consolidar_precipitacion_diaria(calendario, sospechosos)

        self.assertEqual(len(resultado.sensores_cuarentena), 1)
        self.assertTrue(resultado.diario_estacion["precipitacion_diaria_mm"].isna().all())
        self.assertTrue(
            resultado.diario_estacion["motivo_calidad"].eq("SENSOR_EN_CUARENTENA").all()
        )

    def test_extremo_aislado_se_conserva_marcado(self):
        calendario = pd.DataFrame(
            [fila_calendario("0240", "2025-01-01", 174.0)]
        )
        sospechosos = pd.DataFrame(
            [fila_sospechosa("0240", "2025-01-01", "EXTREMO_P99_PARTICION")]
        )
        resultado = consolidar_precipitacion_diaria(calendario, sospechosos)
        fila = resultado.diario_estacion.iloc[0]

        self.assertEqual(fila["precipitacion_diaria_mm"], 174.0)
        self.assertTrue(fila["requiere_revision"])
        self.assertEqual(fila["sensor_seleccionado"], "0240")

    def test_sensores_concordantes_priorizan_0240(self):
        calendario = pd.DataFrame(
            [
                fila_calendario("0257", "2025-01-01", 2.0, cobertura=100.0),
                fila_calendario("0240", "2025-01-01", 2.1, cobertura=95.0),
            ]
        )
        resultado = consolidar_precipitacion_diaria(calendario, pd.DataFrame())
        fila = resultado.diario_estacion.iloc[0]

        self.assertEqual(fila["sensor_seleccionado"], "0240")
        self.assertEqual(fila["precipitacion_diaria_mm"], 2.1)
        self.assertEqual(fila["calidad_dia"], "VALIDO_SENSORES_CONCORDANTES")

    def test_sensores_discrepantes_no_se_promedian(self):
        calendario = pd.DataFrame(
            [
                fila_calendario("0240", "2025-01-01", 0.0),
                fila_calendario("0257", "2025-01-01", 13.9),
            ]
        )
        resultado = consolidar_precipitacion_diaria(calendario, pd.DataFrame())
        fila = resultado.diario_estacion.iloc[0]

        self.assertTrue(pd.isna(fila["precipitacion_diaria_mm"]))
        self.assertTrue(pd.isna(fila["sensor_seleccionado"]))
        self.assertEqual(fila["calidad_dia"], "SENSORES_DISCREPANTES")
        self.assertEqual(fila["diferencia_sensores_mm"], 13.9)


class ClimateDailyConsolidatorNotebookTest(unittest.TestCase):
    def test_run_all_permanece_protegido(self):
        notebook_path = PIPELINE_DIR / "05_ClimateDailyConsolidator.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        namespace = {"__name__": "__daily_consolidator_notebook_test__"}

        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            ast.parse(source, filename=f"cell_{index}")
            exec(compile(source, f"cell_{index}", "exec"), namespace)

        self.assertFalse(namespace["EJECUTAR_CONSOLIDACION"])
        self.assertIsNone(namespace["resultado_consolidacion"])


if __name__ == "__main__":
    unittest.main()
