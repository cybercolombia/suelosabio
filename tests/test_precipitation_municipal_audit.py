import ast
import json
import sys
import unittest
from pathlib import Path

import pandas as pd


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from PrecipitationMunicipalAggregation import (  # noqa: E402
    agregar_precipitacion_municipal,
)
from PrecipitationMunicipalAudit import (  # noqa: E402
    AUDIT_VERSION,
    auditar_precipitacion_municipal,
)


def fila_diaria(estacion, fecha, precipitacion):
    return {
        "variable": "precipitacion",
        "dataset_id": "s54a-sgyg",
        "departamento": "BOYACÁ",
        "codigoestacion": estacion,
        "fecha": fecha,
        "precipitacion_diaria_mm": precipitacion,
        "calidad_dia": "VALIDO" if precipitacion is not None else "SIN_OBSERVACION",
        "requiere_revision": False,
    }


def fila_geografica(estacion, municipio, inicio, fin):
    return {
        "codigoestacion": estacion,
        "fecha_inicio_clima": inicio,
        "fecha_fin_clima": fin,
        "asignacion_canonica": True,
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


class PrecipitationMunicipalAuditTest(unittest.TestCase):
    def setUp(self):
        diario = pd.DataFrame(
            [
                fila_diaria("S1", "2025-01-02", 5.0),
                fila_diaria("S1", "2025-01-03", None),
                fila_diaria("S2", "2025-01-01", 0.0),
                fila_diaria("S3", "2025-01-01", 0.0),
                fila_diaria("S4", "2025-01-01", 30.0),
                fila_diaria("S2", "2025-01-02", 4.0),
                fila_diaria("S3", "2025-01-02", None),
                fila_diaria("S4", "2025-01-02", None),
                fila_diaria("S2", "2025-01-03", None),
                fila_diaria("S3", "2025-01-03", None),
                fila_diaria("S4", "2025-01-03", None),
            ]
        )
        geografia = pd.DataFrame(
            [
                fila_geografica("S1", "15001", "2025-01-02", "2025-01-03"),
                fila_geografica("S2", "15002", "2025-01-01", "2025-01-03"),
                fila_geografica("S3", "15002", "2025-01-01", "2025-01-03"),
                fila_geografica("S4", "15002", "2025-01-01", "2025-01-03"),
            ]
        )
        divipola = pd.DataFrame(
            [
                fila_divipola("15001", "UNO"),
                fila_divipola("15002", "DOS"),
                fila_divipola("15003", "TRES"),
            ]
        )
        self.municipal = agregar_precipitacion_municipal(
            diario,
            geografia,
            divipola,
            "2025-01-01",
            "2025-01-03",
            cobertura_minima_pct=50.0,
        ).diario_municipal

    def test_resume_cobertura_y_periodos_sin_imputar(self):
        resultado = auditar_precipitacion_municipal(self.municipal)
        cobertura = resultado.cobertura_municipios.set_index("codigo_municipio")

        self.assertEqual(AUDIT_VERSION, "auditoria_precipitacion_municipal_v1")
        self.assertEqual(resultado.metricas["filas_municipio_dia"], 9)
        self.assertEqual(resultado.metricas["municipios"], 3)
        self.assertEqual(len(resultado.cobertura_periodos), 9)
        self.assertEqual(
            cobertura.loc["15003", "clasificacion_cobertura"],
            "SIN_ESTACION_CANONICA",
        )
        self.assertEqual(
            cobertura.loc["15002", "cobertura_sobre_dias_esperados_pct"],
            33.33,
        )
        self.assertEqual(
            resultado.metricas["estado"],
            "COMPLETA_CON_REVISION_PENDIENTE",
        )

    def test_identifica_insuficientes_y_sensibilidad_multiestacion(self):
        resultado = auditar_precipitacion_municipal(self.municipal)
        sensibilidad = resultado.sensibilidad_umbrales_lluvia.set_index(
            "umbral_lluvia_mm"
        )

        self.assertEqual(len(resultado.cobertura_insuficiente), 1)
        self.assertEqual(len(resultado.multiestacion_dias), 1)
        self.assertEqual(
            resultado.multiestacion_dias.loc[
                0, "diferencia_absoluta_media_mediana_mm"
            ],
            10.0,
        )
        self.assertEqual(
            sensibilidad.loc[1.0, "dias_clasificacion_diferente"],
            1,
        )
        self.assertEqual(
            resultado.metricas["dias_validos_multiestacion"],
            1,
        )

    def test_rechaza_version_inesperada_y_llaves_repetidas(self):
        version_invalida = self.municipal.copy()
        version_invalida["regla_agregacion"] = "otra_version"
        with self.assertRaisesRegex(ValueError, "version municipal inesperada"):
            auditar_precipitacion_municipal(version_invalida)

        repetida = pd.concat(
            [self.municipal, self.municipal.iloc[[0]]],
            ignore_index=True,
        )
        with self.assertRaisesRegex(ValueError, "llaves municipio-dia repetidas"):
            auditar_precipitacion_municipal(repetida)


class ClimateMunicipalAuditNotebookTest(unittest.TestCase):
    def test_run_all_permanece_protegido_y_separa_entrada_salida(self):
        notebook_path = PIPELINE_DIR / "07_ClimateMunicipalAudit.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        namespace = {"__name__": "__municipal_audit_notebook_test__"}

        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            ast.parse(source, filename=f"cell_{index}")
            exec(compile(source, f"cell_{index}", "exec"), namespace)

        self.assertFalse(namespace["EJECUTAR_AUDITORIA_MUNICIPAL"])
        self.assertFalse(namespace["EJECUTAR_MAPA_ESTACIONES_AQUITANIA"])
        self.assertFalse(namespace["EJECUTAR_HISTOGRAMA_AQUITANIA"])
        self.assertIsNone(namespace["resultado_auditoria_municipal"])
        self.assertEqual(
            namespace["AUDIT_VERSION"],
            "auditoria_precipitacion_municipal_v1",
        )
        self.assertIn(
            "auditorias_clima_municipal",
            str(namespace["OUTPUT_DIR"]),
        )
        self.assertNotEqual(namespace["INPUT_DIR"], namespace["OUTPUT_DIR"])


if __name__ == "__main__":
    unittest.main()
