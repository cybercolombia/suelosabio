import ast
import json
import sys
import unittest
from pathlib import Path

import pandas as pd


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from PrecipitationMunicipalAggregation import (  # noqa: E402
    AGGREGATION_VERSION,
    agregar_precipitacion_municipal,
)


def fila_diaria(estacion, fecha, precipitacion, revision=False):
    return {
        "variable": "precipitacion",
        "dataset_id": "s54a-sgyg",
        "departamento": "BOYACÁ",
        "codigoestacion": estacion,
        "fecha": fecha,
        "precipitacion_diaria_mm": precipitacion,
        "calidad_dia": "VALIDO" if precipitacion is not None else "SIN_OBSERVACION",
        "requiere_revision": revision,
    }


def fila_geografica(estacion, municipio, inicio, fin, canonica=True):
    return {
        "codigoestacion": estacion,
        "fecha_inicio_clima": inicio,
        "fecha_fin_clima": fin,
        "asignacion_canonica": canonica,
        "codigo_municipio_canonico": municipio,
        "municipio_canonico": f"MUNICIPIO {municipio}",
    }


def fila_divipola(codigo, nombre):
    return {
        "codigo_departamento": "15",
        "codigo_municipio": codigo,
        "Nombre Departamento": "BOYACÁ",
        "Nombre Municipio": nombre,
    }


class PrecipitationMunicipalAggregationTest(unittest.TestCase):
    def setUp(self):
        self.diario = pd.DataFrame(
            [
                fila_diaria("S1", "2025-01-02", 5.0),
                fila_diaria("S1", "2025-01-03", None),
                fila_diaria("S2", "2025-01-01", 10.0),
                fila_diaria("S3", "2025-01-01", 20.0),
                fila_diaria("S4", "2025-01-01", 30.0),
                fila_diaria("S2", "2025-01-02", 4.0),
                fila_diaria("S3", "2025-01-02", None),
                fila_diaria("S4", "2025-01-02", None),
                fila_diaria("S2", "2025-01-03", None),
                fila_diaria("S3", "2025-01-03", None),
                fila_diaria("S4", "2025-01-03", None),
                fila_diaria("X1", "2025-01-01", 99.0),
            ]
        )
        self.geografia = pd.DataFrame(
            [
                fila_geografica("S1", "15001", "2025-01-02", "2025-01-03"),
                fila_geografica("S2", "15002", "2025-01-01", "2025-01-03"),
                fila_geografica("S3", "15002", "2025-01-01", "2025-01-03"),
                fila_geografica("S4", "15002", "2025-01-01", "2025-01-03"),
            ]
        )
        self.divipola = pd.DataFrame(
            [
                fila_divipola("15001", "UNO"),
                fila_divipola("15002", "DOS"),
                fila_divipola("15003", "TRES"),
            ]
        )

    def agregar(self):
        return agregar_precipitacion_municipal(
            self.diario,
            self.geografia,
            self.divipola,
            "2025-01-01",
            "2025-01-03",
            cobertura_minima_pct=50.0,
        )

    def test_construye_calendario_completo_y_mediana_multiestacion(self):
        resultado = self.agregar()
        diario = resultado.diario_municipal.set_index(
            ["codigo_municipio", "fecha"]
        )

        self.assertEqual(AGGREGATION_VERSION, "precipitacion_municipio_dia_v1")
        self.assertEqual(len(diario), 9)
        fila = diario.loc[("15002", pd.Timestamp("2025-01-01"))]
        self.assertEqual(fila["estaciones_con_dato"], 3)
        self.assertEqual(fila["precipitacion_media_estaciones_mm"], 20.0)
        self.assertEqual(fila["precipitacion_mediana_estaciones_mm"], 20.0)
        self.assertEqual(fila["precipitacion_municipal_mm"], 20.0)
        self.assertEqual(fila["calidad_municipio_dia"], "VALIDO_MULTIESTACION")

    def test_cobertura_insuficiente_conserva_diagnostico_pero_no_valor(self):
        diario = self.agregar().diario_municipal.set_index(
            ["codigo_municipio", "fecha"]
        )
        fila = diario.loc[("15002", pd.Timestamp("2025-01-02"))]

        self.assertAlmostEqual(fila["cobertura_estaciones_pct"], 100 / 3)
        self.assertEqual(fila["precipitacion_media_estaciones_mm"], 4.0)
        self.assertTrue(pd.isna(fila["precipitacion_municipal_mm"]))
        self.assertTrue(fila["requiere_revision_cobertura"])
        self.assertEqual(
            fila["calidad_municipio_dia"],
            "COBERTURA_INSUFICIENTE",
        )

    def test_distingue_sin_red_sin_estacion_esperada_y_sin_dato(self):
        diario = self.agregar().diario_municipal.set_index(
            ["codigo_municipio", "fecha"]
        )

        self.assertEqual(
            diario.loc[
                ("15003", pd.Timestamp("2025-01-01")),
                "calidad_municipio_dia",
            ],
            "SIN_ESTACIONES_CANONICAS",
        )
        self.assertEqual(
            diario.loc[
                ("15001", pd.Timestamp("2025-01-01")),
                "calidad_municipio_dia",
            ],
            "SIN_ESTACIONES_ESPERADAS_EN_FECHA",
        )
        self.assertEqual(
            diario.loc[
                ("15001", pd.Timestamp("2025-01-03")),
                "calidad_municipio_dia",
            ],
            "SIN_DATOS_ACEPTADOS",
        )

    def test_estacion_no_canonica_no_contribuye_y_queda_en_metricas(self):
        resultado = self.agregar()

        self.assertEqual(resultado.metricas["estaciones_no_canonicas_excluidas"], 1)
        self.assertEqual(resultado.metricas["filas_estacion_dia_excluidas"], 1)
        self.assertEqual(
            resultado.metricas["valores_aceptados_estacion_excluidos"],
            1,
        )
        self.assertFalse(
            resultado.diario_municipal["estaciones_con_dato_codigos"]
            .astype("string")
            .str.contains("X1", na=False)
            .any()
        )

    def test_geografia_no_canonica_falla(self):
        geografia = self.geografia.copy()
        geografia.loc[0, "asignacion_canonica"] = False

        with self.assertRaisesRegex(ValueError, "no canonicas"):
            agregar_precipitacion_municipal(
                self.diario,
                geografia,
                self.divipola,
                "2025-01-01",
                "2025-01-03",
            )

    def test_llave_estacion_dia_repetida_falla(self):
        diario = pd.concat([self.diario, self.diario.iloc[[0]]], ignore_index=True)

        with self.assertRaisesRegex(ValueError, "repetidas"):
            agregar_precipitacion_municipal(
                diario,
                self.geografia,
                self.divipola,
                "2025-01-01",
                "2025-01-03",
            )

    def test_estacion_repetida_entre_departamentos_falla(self):
        repetida = self.diario.iloc[[0]].copy()
        repetida["departamento"] = "CUNDINAMARCA"
        diario = pd.concat([self.diario, repetida], ignore_index=True)

        with self.assertRaisesRegex(ValueError, "mas de un departamento"):
            agregar_precipitacion_municipal(
                diario,
                self.geografia,
                self.divipola,
                "2025-01-01",
                "2025-01-03",
            )


class ClimateMunicipalAggregatorNotebookTest(unittest.TestCase):
    def test_run_all_permanece_protegido_y_versionado(self):
        notebook_path = (
            PIPELINE_DIR
            / "07_Climate_Precipitation_MunicipalAggregator.ipynb"
        )
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        namespace = {"__name__": "__municipal_aggregator_notebook_test__"}

        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            ast.parse(source, filename=f"cell_{index}")
            exec(compile(source, f"cell_{index}", "exec"), namespace)

        self.assertFalse(namespace["EJECUTAR_AGREGACION_MUNICIPAL"])
        self.assertIsNone(namespace["resultado_municipal"])
        self.assertEqual(
            namespace["AGGREGATION_VERSION"],
            "precipitacion_municipio_dia_v1",
        )
        self.assertIn(
            "agregacion=precipitacion_municipio_dia_2024_2025_v1",
            str(namespace["OUTPUT_DIR"]),
        )
        self.assertNotEqual(namespace["OUTPUT_DIR"], namespace["CLIMATE_INPUT_DIR"])
        self.assertNotEqual(
            namespace["OUTPUT_DIR"],
            namespace["GEOGRAPHY_INPUT_DIR"],
        )


if __name__ == "__main__":
    unittest.main()
