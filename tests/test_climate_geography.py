import ast
import json
import sys
import unittest
from pathlib import Path

import pandas as pd


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from ClimateGeography import (  # noqa: E402
    auditar_geografia,
    incorporar_asignaciones_espaciales,
    preparar_tabla_serializable,
    validar_catalogo_ideam,
)


def fila_diaria(estacion, municipio, latitud=5.0, longitud=-73.0):
    return {
        "variable": "precipitacion",
        "dataset_id": "s54a-sgyg",
        "departamento": "CUNDINAMARCA",
        "codigoestacion": estacion,
        "fecha": "2025-01-01",
        "precipitacion_diaria_mm": 2.0,
        "municipios_observados": municipio,
        "nombres_estacion_observados": "ESTACION",
        "latitud_mediana": latitud,
        "longitud_mediana": longitud,
    }


def fila_ideam(
    estacion,
    municipio,
    departamento="Cundinamarca",
    latitud=5.0,
    longitud=-73.0,
):
    return {
        "Codigo": estacion,
        "Nombre": "ESTACION",
        "Categoria": "Pluviometrica",
        "Tecnologia": "Automatica",
        "Estado": "Activa",
        "Departamento": departamento,
        "Municipio": municipio,
        "Altitud": "1,845",
        "LONGITUD": longitud,
        "LATITUD": latitud,
        "Fecha_instalacion": "01/01/2020",
        "Fecha_suspension": pd.NA,
        "Entidad": "IDEAM",
    }


def fila_divipola(codigo, municipio, departamento="CUNDINAMARCA", codigo_dep="25"):
    return {
        "Código Departamento": codigo_dep,
        "Nombre Departamento": departamento,
        "Código Municipio": codigo,
        "Nombre Municipio": municipio,
        "longitud": "-73,0",
        "Latitud": "5,0",
    }


class ClimateGeographyTest(unittest.TestCase):
    def test_tabla_para_mapa_reemplaza_nulos_no_serializables(self):
        original = pd.DataFrame(
            {
                "codigo_municipio": pd.Series(["25839", pd.NA], dtype="string"),
                "fecha_suspension": [pd.Timestamp("2025-01-01"), pd.NaT],
            }
        )

        resultado = preparar_tabla_serializable(original)

        self.assertEqual(resultado.loc[0, "codigo_municipio"], "25839")
        self.assertIsNone(resultado.loc[1, "codigo_municipio"])
        self.assertIsNone(resultado.loc[1, "fecha_suspension"])
        self.assertTrue(pd.isna(original.loc[1, "codigo_municipio"]))

    def test_cruce_exacto_conserva_codigo_y_no_declara_canonico(self):
        diario = pd.DataFrame([fila_diaria("0035060220", "UBALÁ")])
        ideam = pd.DataFrame([fila_ideam("0035060220", "Ubalá")])
        divipola = pd.DataFrame([fila_divipola("25839", "UBALÁ")])

        resultado = auditar_geografia(diario, ideam, divipola)
        fila = resultado.estaciones_candidatas.iloc[0]

        self.assertEqual(fila["codigoestacion"], "0035060220")
        self.assertEqual(fila["codigo_municipio"], "25839")
        self.assertEqual(fila["estado_asignacion"], "CANDIDATO_CATALOGO_OK")
        self.assertFalse(fila["asignacion_canonica"])
        self.assertEqual(resultado.metricas["asignaciones_canonicas"], 0)

    def test_municipio_multiple_y_coordenada_distinta_quedan_en_revision(self):
        diario = pd.DataFrame(
            [fila_diaria("0023067060", "LA PEÑA | NIMAIMA", latitud=5.02)]
        )
        ideam = pd.DataFrame(
            [fila_ideam("0023067060", "La Peña", latitud=5.0)]
        )
        divipola = pd.DataFrame([fila_divipola("25398", "LA PEÑA")])

        resultado = auditar_geografia(
            diario,
            ideam,
            divipola,
            umbral_coordenadas_grados=0.001,
        )
        fila = resultado.estaciones_candidatas.iloc[0]

        self.assertTrue(fila["requiere_revision_geografica"])
        self.assertIn("MUNICIPIO_MULTIPLE", fila["motivos_revision_geografica"])
        self.assertIn("COORDENADA_DIFIERE", fila["motivos_revision_geografica"])

    def test_estacion_bogota_descargada_como_cundinamarca_se_marca(self):
        diario = pd.DataFrame(
            [fila_diaria("2120500204", "BOGOTA D.C", latitud=4.62, longitud=-74.1)]
        )
        ideam = pd.DataFrame(
            [
                fila_ideam(
                    "2120500204",
                    "Bogotá, D.C",
                    departamento="Bogotá",
                    latitud=4.62,
                    longitud=-74.1,
                )
            ]
        )
        divipola = pd.DataFrame(
            [
                fila_divipola(
                    "11001",
                    "BOGOTÁ, D.C.",
                    departamento="BOGOTÁ, D.C.",
                    codigo_dep="11",
                )
            ]
        )

        resultado = auditar_geografia(diario, ideam, divipola)
        fila = resultado.estaciones_candidatas.iloc[0]

        self.assertEqual(fila["codigo_municipio"], "11001")
        self.assertIn(
            "FUERA_ALCANCE_GEOGRAFICO",
            fila["motivos_revision_geografica"],
        )
        self.assertIn(
            "DEPARTAMENTO_DISCREPANTE",
            fila["motivos_revision_geografica"],
        )

    def test_catalogo_ideam_rechaza_codigos_repetidos(self):
        ideam = pd.DataFrame(
            [
                fila_ideam("S1", "Ubalá"),
                fila_ideam("S1", "Ubalá"),
            ]
        )

        with self.assertRaisesRegex(ValueError, "repetidos"):
            validar_catalogo_ideam(ideam)

    def test_cruce_espacial_confirma_resuelve_y_conserva_conflictos(self):
        candidatos = pd.DataFrame(
            {
                "codigoestacion": ["S1", "S2", "S3", "S4"],
                "codigo_municipio": ["25001", pd.NA, "25003", "11001"],
                "departamento_ideam_norm": [
                    "CUNDINAMARCA",
                    "CUNDINAMARCA",
                    "CUNDINAMARCA",
                    "BOGOTA D C",
                ],
                "departamento_ideam_en_alcance": [True, True, True, False],
                "motivos_revision_geografica": [
                    "",
                    "DIVIPOLA_NO_RESUELTA",
                    "",
                    "FUERA_ALCANCE_GEOGRAFICO",
                ],
                "asignacion_metodo": ["CATALOGO"] * 4,
                "asignacion_canonica": [False] * 4,
                "estado_asignacion": ["CANDIDATO"] * 4,
                "requiere_revision_geografica": [False, True, False, True],
            }
        )
        coincidencias = pd.DataFrame(
            {
                "codigoestacion": ["S1", "S2", "S3"],
                "codigo_departamento_poligono": ["25", "25", "25"],
                "codigo_municipio_poligono": ["25001", "25002", "25004"],
                "departamento_poligono": ["CUNDINAMARCA"] * 3,
                "municipio_poligono": ["UNO", "DOS", "CUATRO"],
            }
        )

        resultado = incorporar_asignaciones_espaciales(
            candidatos,
            coincidencias,
        ).set_index("codigoestacion")

        self.assertTrue(resultado.loc["S1", "asignacion_canonica"])
        self.assertEqual(
            resultado.loc["S1", "asignacion_metodo"],
            "PUNTO_EN_POLIGONO_CONFIRMA_CATALOGO",
        )
        self.assertTrue(resultado.loc["S2", "asignacion_canonica"])
        self.assertEqual(
            resultado.loc["S2", "codigo_municipio_canonico"],
            "25002",
        )
        self.assertFalse(resultado.loc["S3", "asignacion_canonica"])
        self.assertIn(
            "CATALOGO_POLIGONO_DISCREPAN",
            resultado.loc["S3", "motivos_revision_geografica"],
        )
        self.assertFalse(resultado.loc["S4", "asignacion_canonica"])
        self.assertIn(
            "SIN_POLIGONO_CONTENEDOR",
            resultado.loc["S4", "motivos_revision_geografica"],
        )

    def test_notebook_run_all_permanece_protegido_y_fuera_de_compartida(self):
        notebook_path = PIPELINE_DIR / "06_ClimateGeographyAudit.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        namespace = {"__name__": "__climate_geography_notebook_test__"}
        codigo = "\n".join(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        )

        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            ast.parse(source, filename=f"cell_{index}")
            exec(compile(source, f"cell_{index}", "exec"), namespace)

        self.assertFalse(namespace["EJECUTAR_AUDITORIA_GEOGRAFICA"])
        self.assertIsNone(namespace["resultado_geografia"])
        self.assertNotEqual(
            namespace["OUTPUT_DIR"],
            namespace["SHARED_SOURCE_ROOT"],
        )
        self.assertNotIn(
            namespace["SHARED_SOURCE_ROOT"],
            namespace["OUTPUT_DIR"].parents,
        )
        self.assertIn("importlib.reload(ClimateGeography)", codigo)
        self.assertIn("importlib.reload(ClimateProcessingUtils)", codigo)


if __name__ == "__main__":
    unittest.main()
