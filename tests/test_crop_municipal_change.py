import sys
import unittest
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = REPO_ROOT / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from CropMunicipalChange import (  # noqa: E402
    aggregate_crop_municipal_period,
    audit_crop_geography,
)
from tests.test_crop_yield_processing import eva_row  # noqa: E402


class CropMunicipalChangeTest(unittest.TestCase):
    def test_siembra_se_conserva_cuando_cosecha_es_cero(self):
        row = eva_row(harvested=0, production=0, yield_value=0)
        result = aggregate_crop_municipal_period(pd.DataFrame([row]))

        target = result.municipal_period.iloc[0]
        self.assertEqual(target["area_sembrada_ha"], 12)
        self.assertEqual(target["area_cosechada_ha"], 0)
        self.assertTrue(pd.isna(target["rendimiento_t_ha"]))

    def test_rendimiento_es_razon_de_totales(self):
        rows = [
            eva_row(harvested=10, production=200, yield_value=20),
            eva_row(
                disaggregation="Papa criolla",
                harvested=5,
                production=150,
                yield_value=30,
            ),
        ]
        result = aggregate_crop_municipal_period(pd.DataFrame(rows))

        target = result.municipal_period.iloc[0]
        self.assertAlmostEqual(target["rendimiento_t_ha"], 350 / 15)
        self.assertTrue(target["requiere_revision_desagregacion"])

    def test_cambio_compara_mismo_tipo_periodo(self):
        first = eva_row(period="2022A")
        second = eva_row(period="2023A")
        second["a_o"] = "2023"
        second["rea_sembrada"] = "18"
        result = aggregate_crop_municipal_period(pd.DataFrame([first, second]))

        self.assertEqual(len(result.changes), 1)
        change = result.changes.iloc[0]
        self.assertEqual(change["tipo_periodo"], "A")
        self.assertEqual(change["area_sembrada_ha_cambio_abs"], 6)
        self.assertEqual(change["area_sembrada_ha_estado"], "AUMENTA")

    def test_periodo_anual_transitorio_se_excluye(self):
        result = aggregate_crop_municipal_period(
            pd.DataFrame([eva_row(period="2022", cycle="Transitorio")])
        )

        self.assertTrue(result.municipal_period.empty)
        self.assertIn("CICLO_PERIODO_INCOMPATIBLE", set(result.issues["motivo"]))

    def test_geografia_se_une_por_codigo_no_por_nombre(self):
        result = aggregate_crop_municipal_period(pd.DataFrame([eva_row()]))
        geography = pd.DataFrame(
            [
                {
                    "codigo_municipio_poligono": "15001",
                    "municipio_poligono": "TUNJA OFICIAL",
                    "departamento_poligono": "BOYACA",
                    "geometry": b"test",
                }
            ]
        )
        audit = audit_crop_geography(result.municipal_period, geography)

        self.assertEqual(audit.summary.loc[0, "municipios_sin_geometria"], 0)
        self.assertEqual(
            audit.summary.loc[0, "diferencias_nombre_con_codigo_coincidente"], 1
        )


if __name__ == "__main__":
    unittest.main()
