import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = REPO_ROOT / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from ClimateProcessingUtils import (  # noqa: E402
    PartitionSpec,
    descubrir_partes_parquet,
    escribir_json_atomico,
    escribir_parquet_atomico,
    escribir_texto_atomico,
    ruta_particion_cruda,
    ruta_particion_diaria,
)
from PrecipitationRules import procesar_precipitacion  # noqa: E402


def observacion(
    estacion,
    sensor,
    fecha,
    valor,
    *,
    municipio="TEST",
    unidad="mm",
    departamento="CUNDINAMARCA",
    latitud=4.5,
    longitud=-74.1,
):
    return {
        "codigoestacion": estacion,
        "codigosensor": sensor,
        "dataset_id": "s54a-sgyg",
        "departamento": departamento,
        "descripcionsensor": "PRECIPITACION",
        "fechaobservacion": fecha,
        "latitud": latitud,
        "longitud": longitud,
        "municipio": municipio,
        "nombreestacion": f"ESTACION {estacion}",
        "unidadmedida": unidad,
        "valorobservado": valor,
        "zonahidrografica": "ZONA",
    }


class ClimateProcessingUtilsTest(unittest.TestCase):
    def test_rutas_y_unicode_son_deterministas(self):
        spec = PartitionSpec(
            "Precipitacion",
            "S54A-SGYG",
            "CUNDINAMARCA",
            2025,
            2,
        )
        root = Path("/tmp/eco2026_processed")
        self.assertEqual(
            ruta_particion_cruda(root, spec),
            root
            / "clima_crudo"
            / "variable=precipitacion"
            / "fuente=s54a-sgyg"
            / "departamento=CUNDINAMARCA"
            / "anio=2025"
            / "mes=02",
        )
        self.assertIn("clima_diario_sensor", str(ruta_particion_diaria(root, spec)))

        boyaca = PartitionSpec("precipitacion", "s54a-sgyg", "BOYACA", 2025, 1)
        self.assertEqual(boyaca.departamento, "BOYACÁ")
        self.assertIn("departamento=BOYACÁ", str(ruta_particion_cruda(root, boyaca)))

    def test_escrituras_atomicas_y_secuencia_de_partes(self):
        with tempfile.TemporaryDirectory() as temporal:
            root = Path(temporal)
            tabla = pd.DataFrame({"valor": [1, 2]})
            destino = root / "part-00000.parquet"
            escribir_parquet_atomico(tabla, destino)
            self.assertEqual(descubrir_partes_parquet(root), [destino])
            with self.assertRaises(FileExistsError):
                escribir_parquet_atomico(tabla, destino)

            manifiesto = root / "manifest.json"
            escribir_json_atomico({"estado": "COMPLETA"}, manifiesto)
            self.assertEqual(json.loads(manifiesto.read_text())["estado"], "COMPLETA")

            reporte = root / "reporte.md"
            escribir_texto_atomico("# Reporte\n", reporte)
            self.assertEqual(reporte.read_text(encoding="utf-8"), "# Reporte\n")


class PrecipitationRulesTest(unittest.TestCase):
    def setUp(self):
        self.spec = PartitionSpec(
            "precipitacion",
            "s54a-sgyg",
            "CUNDINAMARCA",
            2025,
            2,
        )

    def test_suma_diaria_separa_sensores_e_infiere_cadencia(self):
        filas = []
        for minuto, valor in [(0, 0.0), (5, 0.2), (10, 0.3)]:
            filas.append(
                observacion("E1", "0240", f"2025-02-01 00:{minuto:02d}:00", valor)
            )
        for minuto, valor in [(0, 0.0), (1, 0.1), (2, 0.0)]:
            filas.append(
                observacion("E1", "0257", f"2025-02-01 00:{minuto:02d}:00", valor)
            )

        resultado = procesar_precipitacion(pd.DataFrame(filas), self.spec)
        diario = resultado.diario.set_index("codigosensor")

        self.assertEqual(len(diario), 2)
        self.assertAlmostEqual(diario.loc["0240", "precipitacion_observada_mm"], 0.5)
        self.assertAlmostEqual(diario.loc["0257", "precipitacion_observada_mm"], 0.1)
        self.assertTrue(diario["precipitacion_diaria_mm"].isna().all())
        self.assertTrue(
            diario["calidad_dia"].eq("PENDIENTE_REGLA_COBERTURA").all()
        )
        self.assertEqual(diario.loc["0240", "intervalo_moda_segundos"], 300)
        self.assertEqual(diario.loc["0257", "intervalo_moda_segundos"], 60)
        self.assertEqual(diario.loc["0240", "observaciones_esperadas"], 288)
        self.assertEqual(resultado.metricas["filas_diarias_salida"], 2)

    def test_rechaza_invalidos_y_no_promedia_conflictos(self):
        filas = [
            observacion("E1", "0240", "2025-02-01 00:00:00", 0.1),
            observacion("E1", "0240", "2025-02-01 00:00:00", 0.2),
            observacion("E2", "0240", "2025-02-01 00:00:00", -1),
            observacion("E3", "0240", "2025-03-01 00:00:00", 1),
        ]
        resultado = procesar_precipitacion(pd.DataFrame(filas), self.spec)

        self.assertTrue(resultado.diario.empty)
        self.assertEqual(resultado.metricas["claves_conflictivas"], 1)
        self.assertEqual(resultado.metricas["filas_conflictivas_excluidas"], 2)
        self.assertEqual(resultado.metricas["filas_rechazadas"], 2)
        motivos = "|".join(resultado.rechazados["motivo_rechazo"].tolist())
        self.assertIn("valor_negativo", motivos)
        self.assertIn("mes_fuera_particion", motivos)

    def test_rechaza_fuente_y_unidad_nulas(self):
        fuente_nula = observacion("E1", "0240", "2025-02-01", 0.1)
        fuente_nula["dataset_id"] = None
        unidad_nula = observacion("E2", "0240", "2025-02-01", 0.1, unidad=None)

        resultado = procesar_precipitacion(
            pd.DataFrame([fuente_nula, unidad_nula]),
            self.spec,
        )

        self.assertEqual(resultado.metricas["filas_rechazadas"], 2)
        motivos = "|".join(resultado.rechazados["motivo_rechazo"].tolist())
        self.assertIn("fuente_fuera_particion", motivos)
        self.assertIn("unidad_no_mm", motivos)

    def test_rechaza_descripcion_de_otra_variable(self):
        fila = observacion("E1", "0240", "2025-02-01", 0.1)
        fila["descripcionsensor"] = "TEMPERATURA DEL AIRE"

        resultado = procesar_precipitacion(pd.DataFrame([fila]), self.spec)

        self.assertEqual(resultado.metricas["filas_rechazadas"], 1)
        self.assertIn(
            "sensor_no_precipitacion",
            resultado.rechazados.iloc[0]["motivo_rechazo"],
        )

    def test_conserva_par_sin_cadencia_evaluable(self):
        filas = [
            observacion("E1", "0240", "2025-02-01 00:00:00", 0.1),
            observacion("E2", "0240", "2025-02-01 00:00:00", 0.0),
            observacion("E2", "0240", "2025-02-01 00:10:00", 0.2),
        ]

        resultado = procesar_precipitacion(pd.DataFrame(filas), self.spec)
        cadencias = resultado.cadencias.set_index("codigoestacion")

        self.assertEqual(len(cadencias), 2)
        self.assertTrue(pd.isna(cadencias.loc["E1", "intervalo_moda_segundos"]))
        self.assertFalse(
            resultado.diario.set_index("codigoestacion").loc["E1", "cobertura_evaluable"]
        )

    def test_elimina_duplicados_exactos_y_clave_con_mismo_valor(self):
        primera = observacion("E1", "0240", "2025-02-01 00:00:00", 0.2)
        exacta = dict(primera)
        metadato_distinto = observacion(
            "E1",
            "0240",
            "2025-02-01 00:00:00",
            0.2,
            municipio="OTRA ETIQUETA",
        )
        siguiente = observacion("E1", "0240", "2025-02-01 00:10:00", 0.3)

        resultado = procesar_precipitacion(
            pd.DataFrame([primera, exacta, metadato_distinto, siguiente]),
            self.spec,
        )

        self.assertEqual(resultado.metricas["filas_duplicadas_exactas_eliminadas"], 1)
        self.assertEqual(resultado.metricas["filas_clave_repetida_eliminadas"], 1)
        self.assertEqual(len(resultado.duplicados_eliminados), 2)
        self.assertAlmostEqual(
            resultado.diario.iloc[0]["precipitacion_observada_mm"],
            0.5,
        )


class ClimateDailyNotebookIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        notebook_path = PIPELINE_DIR / "03_ClimateDailyProcessor.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        cls.cells = {cell.get("id"): "".join(cell["source"]) for cell in notebook["cells"]}

    def cargar_controlador(self):
        namespace = {"__name__": "__notebook_test__"}
        for cell_id in ("daily_bootstrap", "daily_config", "daily_processing_functions"):
            exec(compile(self.cells[cell_id], cell_id, "exec"), namespace)
        return namespace

    def test_procesa_particion_y_reanuda_sin_duplicar(self):
        namespace = self.cargar_controlador()
        with tempfile.TemporaryDirectory() as temporal:
            root = Path(temporal)
            namespace["PROCESSED_ROOT"] = root
            namespace["WORKER_ID"] = "test_worker"
            namespace["SOBRESCRIBIR_RESULTADOS"] = False
            spec = PartitionSpec(
                "precipitacion",
                "s54a-sgyg",
                "CUNDINAMARCA",
                2025,
                2,
            )
            input_dir = ruta_particion_cruda(root, spec)
            input_dir.mkdir(parents=True)
            pd.DataFrame(
                [
                    observacion("E1", "0240", "2025-02-01 00:00:00", 0.1),
                    observacion("E1", "0240", "2025-02-01 00:05:00", 0.2),
                    observacion("E1", "0257", "2025-02-01 00:00:00", 0.4),
                    observacion("E1", "0257", "2025-02-01 00:01:00", 0.0),
                ]
            ).to_parquet(input_dir / "part-00000.parquet", index=False)

            primera = namespace["procesar_particion"](spec)
            segunda = namespace["procesar_particion"](spec)
            output_dir = ruta_particion_diaria(root, spec)
            manifiesto = json.loads(
                (output_dir / "manifest.json").read_text(encoding="utf-8")
            )
            diario = pd.read_parquet(output_dir / "observaciones_diarias.parquet")

            self.assertEqual(primera["estado"], "completa")
            self.assertEqual(segunda["estado"], "omitida_ya_completa")
            self.assertEqual(manifiesto["estado"], "COMPLETA")
            self.assertEqual(manifiesto["entrada"]["filas"], 4)
            self.assertEqual(len(diario), 2)
            self.assertAlmostEqual(diario["precipitacion_observada_mm"].sum(), 0.7)
            self.assertTrue(diario["precipitacion_diaria_mm"].isna().all())

    def test_no_reanuda_salida_incompleta_silenciosamente(self):
        namespace = self.cargar_controlador()
        with tempfile.TemporaryDirectory() as temporal:
            root = Path(temporal)
            namespace["PROCESSED_ROOT"] = root
            namespace["SOBRESCRIBIR_RESULTADOS"] = False
            spec = PartitionSpec(
                "precipitacion",
                "s54a-sgyg",
                "BOYACA",
                2025,
                1,
            )
            output_dir = ruta_particion_diaria(root, spec)
            output_dir.mkdir(parents=True)
            (output_dir / "manifest.json").write_text(
                json.dumps({"estado": "INICIADA"}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "salida incompleta"):
                namespace["procesar_particion"](spec)


if __name__ == "__main__":
    unittest.main()
