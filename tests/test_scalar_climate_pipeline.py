import sys
import unittest
from pathlib import Path

import pandas as pd


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from AtmosphericPressureDailyAudit import (  # noqa: E402
    auditar_presion_atmosferica_diaria,
)
from AtmosphericPressureRules import procesar_presion_atmosferica  # noqa: E402
from ClimateProcessingUtils import PartitionSpec  # noqa: E402
from ScalarDailyConsolidation import consolidar_escalar_diario  # noqa: E402
from ScalarMunicipalAggregation import agregar_escalar_municipal  # noqa: E402
from WindSpeedRules import procesar_velocidad_viento  # noqa: E402


def observacion(variable, sensor, unidad, descripcion, valor, fecha):
    dataset = {
        "presion_atmosferica": "62tk-nxj5",
        "velocidad_viento": "sgfv-3yp8",
    }[variable]
    return {
        "codigoestacion": "E1",
        "codigosensor": sensor,
        "dataset_id": dataset,
        "departamento": "CUNDINAMARCA",
        "descripcionsensor": descripcion,
        "fechaobservacion": fecha,
        "latitud": 4.5,
        "longitud": -74.1,
        "municipio": "M1",
        "nombreestacion": "Estación uno",
        "unidadmedida": unidad,
        "valorobservado": valor,
        "zonahidrografica": "Z1",
    }


class ScalarClimatePipelineTest(unittest.TestCase):
    def test_presion_calcula_media_diaria_y_audita(self):
        raw = pd.DataFrame(
            [
                observacion(
                    "presion_atmosferica",
                    "0255",
                    "hPa",
                    "PRESIÓN ATMOSFÉRICA",
                    900.0,
                    "2025-01-01 00:00:00",
                ),
                observacion(
                    "presion_atmosferica",
                    "0255",
                    "hPa",
                    "PRESIÓN ATMOSFÉRICA",
                    902.0,
                    "2025-01-01 01:00:00",
                ),
            ]
        )
        spec = PartitionSpec(
            "presion_atmosferica",
            "62tk-nxj5",
            "CUNDINAMARCA",
            2025,
            1,
        )
        procesado = procesar_presion_atmosferica(raw, spec)
        self.assertAlmostEqual(
            procesado.diario.iloc[0]["valor_principal_observado"],
            901.0,
        )
        auditado = auditar_presion_atmosferica_diaria(procesado.diario)
        self.assertIn("valor_principal_observado", auditado.calendario.columns)
        self.assertNotIn(
            "temperatura_principal_observada_c",
            auditado.calendario.columns,
        )

    def test_viento_rechaza_sensor_fuera_de_contrato(self):
        raw = pd.DataFrame(
            [
                observacion(
                    "velocidad_viento",
                    "9999",
                    "m/s",
                    "VELOCIDAD DEL VIENTO",
                    3.0,
                    "2025-01-01 00:00:00",
                )
            ]
        )
        spec = PartitionSpec(
            "velocidad_viento",
            "sgfv-3yp8",
            "CUNDINAMARCA",
            2025,
            1,
        )
        resultado = procesar_velocidad_viento(raw, spec)
        self.assertTrue(resultado.diario.empty)
        self.assertIn(
            "sensor_fuera_contrato",
            resultado.rechazados.iloc[0]["motivo_rechazo"],
        )

    def test_auditoria_escalar_no_publica_etiquetas_de_temperatura(self):
        raw = pd.DataFrame(
            [
                observacion(
                    "presion_atmosferica",
                    "0255",
                    "hPa",
                    "PRESIÓN ATMOSFÉRICA",
                    450.0,
                    "2025-01-01 00:00:00",
                ),
                observacion(
                    "presion_atmosferica",
                    "0255",
                    "hPa",
                    "PRESIÓN ATMOSFÉRICA",
                    450.0,
                    "2025-01-01 01:00:00",
                ),
            ]
        )
        spec = PartitionSpec(
            "presion_atmosferica",
            "62tk-nxj5",
            "CUNDINAMARCA",
            2025,
            1,
        )
        diario = procesar_presion_atmosferica(raw, spec).diario
        sospechosos = auditar_presion_atmosferica_diaria(diario).valores_sospechosos
        self.assertEqual(sospechosos.iloc[0]["motivos_revision"], "VALOR_MUY_BAJO")
        self.assertNotIn(
            "TEMPERATURA",
            sospechosos.iloc[0]["motivos_revision"],
        )

    def test_consolidacion_no_promedia_sensores_discrepantes(self):
        calendario = pd.DataFrame(
            [
                {
                    "variable": "presion_atmosferica",
                    "dataset_id": "62tk-nxj5",
                    "departamento": "CUNDINAMARCA",
                    "codigoestacion": "E1",
                    "codigosensor": sensor,
                    "fecha": pd.Timestamp("2025-01-01"),
                    "es_dia_observado": True,
                    "valor_principal_observado": valor,
                    "cobertura_observada_pct": 100.0,
                    "cobertura_evaluable": True,
                    "municipios_observados": "M1",
                    "nombres_estacion_observados": "Estación uno",
                    "latitud_mediana": 4.5,
                    "longitud_mediana": -74.1,
                }
                for sensor, valor in (("0255", 900.0), ("0256", 910.0))
            ]
        )
        resultado = consolidar_escalar_diario(calendario)
        fila = resultado.diario_estacion.iloc[0]
        self.assertTrue(pd.isna(fila["valor_diario"]))
        self.assertEqual(fila["calidad_dia"], "SENSORES_DISCREPANTES")

    def test_agregado_municipal_conserva_variable_y_unidad(self):
        diario = pd.DataFrame(
            [
                {
                    "variable": "temperatura_ambiente",
                    "dataset_id": "sbwg-7ju4",
                    "departamento": "CUNDINAMARCA",
                    "codigoestacion": "E1",
                    "fecha": pd.Timestamp("2025-01-01"),
                    "valor_diario": 20.0,
                    "unidad_valor": "°C",
                    "calidad_dia": "VALIDO_SENSOR_UNICO",
                    "requiere_revision": False,
                }
            ]
        )
        estaciones = pd.DataFrame(
            [
                {
                    "codigoestacion": "E1",
                    "fecha_inicio_clima": pd.Timestamp("2025-01-01"),
                    "fecha_fin_clima": pd.Timestamp("2025-01-01"),
                    "asignacion_canonica": True,
                    "codigo_municipio_canonico": "25001",
                    "municipio_canonico": "M1",
                }
            ]
        )
        divipola = pd.DataFrame(
            [
                {
                    "codigo_departamento": "25",
                    "codigo_municipio": "25001",
                    "Nombre Departamento": "CUNDINAMARCA",
                    "Nombre Municipio": "M1",
                }
            ]
        )
        resultado = agregar_escalar_municipal(
            diario,
            estaciones,
            divipola,
            "2025-01-01",
            "2025-01-01",
        )
        fila = resultado.diario_municipal.iloc[0]
        self.assertEqual(fila["valor_municipal"], 20.0)
        self.assertEqual(fila["variable"], "temperatura_ambiente")
        self.assertEqual(fila["unidad_valor"], "°C")


if __name__ == "__main__":
    unittest.main()
