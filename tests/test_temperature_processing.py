import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from ClimateProcessingUtils import PartitionSpec  # noqa: E402
from ClimateProcessingUtils import ruta_particion_cruda, ruta_particion_diaria  # noqa: E402
from TemperatureRules import procesar_temperatura  # noqa: E402


CONTRATOS = {
    "temperatura_ambiente": ("sbwg-7ju4", "0068", "TEMPERATURA DEL AIRE A 2 m"),
    "temperatura_minima": (
        "afdg-3zpb",
        "0070",
        "TEMPERATURA MÍNIMA DEL AIRE A 2 m",
    ),
    "temperatura_maxima": (
        "ccvq-rp9s",
        "0069",
        "TEMPERATURA DEL AIRE MÁXIMA A 2 m",
    ),
}


def observacion(variable, fecha, valor, *, sensor=None, dataset_id=None, descripcion=None):
    fuente, sensor_contrato, descripcion_contrato = CONTRATOS[variable]
    return {
        "codigoestacion": "E1",
        "codigosensor": sensor or sensor_contrato,
        "dataset_id": dataset_id or fuente,
        "departamento": "CUNDINAMARCA",
        "descripcionsensor": descripcion or descripcion_contrato,
        "fechaobservacion": fecha,
        "latitud": 4.5,
        "longitud": -74.1,
        "municipio": "TEST",
        "nombreestacion": "ESTACION TEST",
        "unidadmedida": "°C",
        "valorobservado": valor,
        "zonahidrografica": "ZONA",
    }


class TemperatureRulesTest(unittest.TestCase):
    def spec(self, variable):
        return PartitionSpec(
            variable,
            CONTRATOS[variable][0],
            "CUNDINAMARCA",
            2025,
            1,
        )

    def test_ambiente_calcula_estadisticos_sin_sumar(self):
        filas = [
            observacion("temperatura_ambiente", "2025-01-01 00:00:00", 10.0),
            observacion("temperatura_ambiente", "2025-01-01 01:00:00", 20.0),
            observacion("temperatura_ambiente", "2025-01-01 02:00:00", 30.0),
        ]

        resultado = procesar_temperatura(
            pd.DataFrame(filas), self.spec("temperatura_ambiente")
        )
        diario = resultado.diario.iloc[0]

        self.assertEqual(diario["estadistico_temperatura"], "MEDIA")
        self.assertAlmostEqual(diario["temperatura_principal_observada_c"], 20.0)
        self.assertAlmostEqual(diario["temperatura_media_observada_c"], 20.0)
        self.assertAlmostEqual(diario["temperatura_minima_observada_c"], 10.0)
        self.assertAlmostEqual(diario["temperatura_maxima_observada_c"], 30.0)
        self.assertAlmostEqual(diario["amplitud_termica_observada_c"], 20.0)
        self.assertEqual(diario["intervalo_moda_segundos"], 3600)
        self.assertTrue(pd.isna(diario["temperatura_diaria_c"]))

    def test_minima_y_maxima_usan_el_extremo_correspondiente(self):
        valores = [12.0, 8.0, 21.0]
        casos = {
            "temperatura_minima": ("MINIMO", 8.0),
            "temperatura_maxima": ("MAXIMO", 21.0),
        }
        for variable, (estadistico, esperado) in casos.items():
            with self.subTest(variable=variable):
                filas = [
                    observacion(variable, f"2025-01-01 0{i}:00:00", valor)
                    for i, valor in enumerate(valores)
                ]
                resultado = procesar_temperatura(pd.DataFrame(filas), self.spec(variable))
                diario = resultado.diario.iloc[0]
                self.assertEqual(diario["estadistico_temperatura"], estadistico)
                self.assertAlmostEqual(
                    diario["temperatura_principal_observada_c"], esperado
                )

    def test_elimina_duplicados_y_excluye_conflictos(self):
        primera = observacion(
            "temperatura_maxima", "2025-01-01 00:00:00", 20.0
        )
        filas = [
            primera,
            dict(primera),
            observacion("temperatura_maxima", "2025-01-01 01:00:00", 21.0),
            observacion("temperatura_maxima", "2025-01-01 01:00:00", 22.0),
            observacion("temperatura_maxima", "2025-01-01 02:00:00", 23.0),
        ]

        resultado = procesar_temperatura(
            pd.DataFrame(filas), self.spec("temperatura_maxima")
        )

        self.assertEqual(resultado.metricas["filas_duplicadas_exactas_eliminadas"], 1)
        self.assertEqual(resultado.metricas["claves_conflictivas"], 1)
        self.assertEqual(resultado.metricas["filas_conflictivas_excluidas"], 2)
        self.assertEqual(resultado.metricas["filas_validas_agregadas"], 2)
        self.assertAlmostEqual(
            resultado.diario.iloc[0]["temperatura_maxima_observada_c"], 23.0
        )

    def test_rechaza_variable_unidad_sensor_y_rango_incompatibles(self):
        unidad = observacion("temperatura_ambiente", "2025-01-01", 15.0)
        unidad["unidadmedida"] = "mm"
        sensor = observacion(
            "temperatura_ambiente", "2025-01-01 01:00:00", 15.0, sensor="0070"
        )
        rango = observacion("temperatura_ambiente", "2025-01-01 02:00:00", 99.0)
        descripcion = observacion(
            "temperatura_ambiente",
            "2025-01-01 03:00:00",
            15.0,
            descripcion="TEMPERATURA MÍNIMA DEL AIRE A 2 m",
        )

        resultado = procesar_temperatura(
            pd.DataFrame([unidad, sensor, rango, descripcion]),
            self.spec("temperatura_ambiente"),
        )
        motivos = "|".join(resultado.rechazados["motivo_rechazo"])

        self.assertEqual(resultado.metricas["filas_rechazadas"], 4)
        self.assertIn("unidad_no_celsius", motivos)
        self.assertIn("sensor_fuera_contrato", motivos)
        self.assertIn("temperatura_fuera_rango_operativo", motivos)
        self.assertIn("descripcion_no_corresponde_variable", motivos)

    def test_rechaza_fuente_incompatible_con_variable(self):
        spec = PartitionSpec(
            "temperatura_ambiente",
            "afdg-3zpb",
            "CUNDINAMARCA",
            2025,
            1,
        )
        fila = observacion("temperatura_ambiente", "2025-01-01", 15.0)

        with self.assertRaisesRegex(ValueError, "requiere la fuente"):
            procesar_temperatura(pd.DataFrame([fila]), spec)

    def test_no_infiere_cadencia_entre_dias_separados(self):
        filas = [
            observacion("temperatura_ambiente", "2025-01-01 00:00:00", 10.0),
            observacion("temperatura_ambiente", "2025-01-04 00:00:00", 15.0),
            observacion("temperatura_ambiente", "2025-01-08 00:00:00", 20.0),
        ]

        resultado = procesar_temperatura(
            pd.DataFrame(filas), self.spec("temperatura_ambiente")
        )

        self.assertTrue(resultado.cadencias["intervalo_moda_segundos"].isna().all())
        self.assertFalse(resultado.diario["cobertura_evaluable"].any())
        self.assertTrue(resultado.diario["observaciones_esperadas"].isna().all())
        self.assertTrue(resultado.diario["cobertura_observada_pct"].isna().all())

    def test_cadencia_no_reconocida_no_produce_cobertura(self):
        filas = [
            observacion("temperatura_ambiente", "2025-01-01 00:00:00", 10.0),
            observacion("temperatura_ambiente", "2025-01-01 00:43:00", 15.0),
            observacion("temperatura_ambiente", "2025-01-01 01:26:00", 20.0),
        ]

        resultado = procesar_temperatura(
            pd.DataFrame(filas), self.spec("temperatura_ambiente")
        )
        diario = resultado.diario.iloc[0]

        self.assertEqual(diario["intervalo_moda_segundos"], 2580)
        self.assertFalse(diario["cadencia_observada_conocida"])
        self.assertFalse(diario["cobertura_evaluable"])
        self.assertTrue(pd.isna(diario["observaciones_esperadas"]))
        self.assertTrue(pd.isna(diario["cobertura_observada_pct"]))

    def test_calcula_cadencia_por_dia_si_el_sensor_cambia_frecuencia(self):
        filas = [
            observacion("temperatura_ambiente", "2025-01-01 00:00:00", 10.0),
            observacion("temperatura_ambiente", "2025-01-01 01:00:00", 15.0),
            observacion("temperatura_ambiente", "2025-01-01 02:00:00", 20.0),
            observacion("temperatura_ambiente", "2025-01-02 00:00:00", 10.0),
            observacion("temperatura_ambiente", "2025-01-02 00:10:00", 15.0),
            observacion("temperatura_ambiente", "2025-01-02 00:20:00", 20.0),
        ]

        resultado = procesar_temperatura(
            pd.DataFrame(filas), self.spec("temperatura_ambiente")
        )
        diario = resultado.diario.set_index("fecha")

        self.assertEqual(
            diario.loc[pd.Timestamp("2025-01-01"), "intervalo_moda_segundos"],
            3600,
        )
        self.assertEqual(
            diario.loc[pd.Timestamp("2025-01-02"), "intervalo_moda_segundos"],
            600,
        )
        self.assertEqual(
            diario.loc[pd.Timestamp("2025-01-01"), "observaciones_esperadas"],
            24,
        )
        self.assertEqual(
            diario.loc[pd.Timestamp("2025-01-02"), "observaciones_esperadas"],
            144,
        )


class TemperatureNotebookIntegrationTest(unittest.TestCase):
    def test_procesador_despacha_temperatura_ambiente(self):
        notebook_path = PIPELINE_DIR / "03_ClimateDailyProcessor.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        celdas = {cell.get("id"): "".join(cell["source"]) for cell in notebook["cells"]}
        config = celdas["daily_config"].replace(
            "VARIABLE_NOMBRE = 'precipitacion'",
            "VARIABLE_NOMBRE = 'temperatura_ambiente'",
        ).replace(
            "DATASET_ID = 's54a-sgyg'",
            "DATASET_ID = 'sbwg-7ju4'",
        )
        namespace = {"__name__": "__temperature_notebook_test__"}
        for nombre, codigo in (
            ("daily_bootstrap", celdas["daily_bootstrap"]),
            ("daily_config", config),
            ("daily_processing_functions", celdas["daily_processing_functions"]),
        ):
            exec(compile(codigo, nombre, "exec"), namespace)

        with tempfile.TemporaryDirectory() as temporal:
            root = Path(temporal)
            namespace["PROCESSED_ROOT"] = root
            namespace["WORKER_ID"] = "test_temperature"
            spec = PartitionSpec(
                "temperatura_ambiente",
                "sbwg-7ju4",
                "CUNDINAMARCA",
                2025,
                1,
            )
            entrada = ruta_particion_cruda(root, spec)
            entrada.mkdir(parents=True)
            pd.DataFrame(
                [
                    observacion(
                        "temperatura_ambiente", "2025-01-01 00:00:00", 10.0
                    ),
                    observacion(
                        "temperatura_ambiente", "2025-01-01 01:00:00", 20.0
                    ),
                ]
            ).to_parquet(entrada / "part-00000.parquet", index=False)

            resumen = namespace["procesar_particion"](spec)
            salida = pd.read_parquet(
                ruta_particion_diaria(root, spec) / "observaciones_diarias.parquet"
            )

        self.assertEqual(resumen["estado"], "completa")
        self.assertEqual(resumen["regla_version"], "temperatura_diaria_v2")
        self.assertAlmostEqual(salida.iloc[0]["temperatura_media_observada_c"], 15.0)


if __name__ == "__main__":
    unittest.main()
