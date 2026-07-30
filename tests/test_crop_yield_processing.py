import sys
import unittest
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = REPO_ROOT / "notebooks" / "ClimatePipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from CropYieldProcessing import (  # noqa: E402
    TARGET_KEY,
    audit_curated_eva,
    audit_raw_eva,
    curate_eva,
    normalize_eva,
)


def eva_row(
    *,
    municipality_code="15001",
    municipality="Tunja",
    crop="Papa",
    disaggregation="Papa demás variedades",
    period="2022A",
    cycle="Transitorio",
    state="En fresco",
    harvested=10.0,
    production=200.0,
    yield_value=20.0,
):
    return {
        "c_digo_dane_departamento": "15",
        "departamento": "Boyacá",
        "c_digo_dane_municipio": municipality_code,
        "municipio": municipality,
        "grupo_cultivo": "Tubérculos",
        "subgrupo": "Papa",
        "cultivo": crop,
        "desagregaci_n_cultivo": disaggregation,
        "a_o": "2022",
        "periodo": period,
        "rea_sembrada": "12",
        "rea_cosechada": str(harvested),
        "producci_n": str(production),
        "rendimiento": str(yield_value),
        "ciclo_del_cultivo": cycle,
        "estado_f_sico_del_cultivo": state,
        "c_digo_del_cultivo": "101",
        "nombre_cient_fico_del_cultivo": "Solanum tuberosum",
        "dataset_id": "uejq-wxrr",
    }


class CropYieldProcessingTest(unittest.TestCase):
    def test_normalization_preserves_dane_codes_as_text(self):
        normalized = normalize_eva(pd.DataFrame([eva_row()]))

        self.assertEqual(normalized.loc[0, "codigo_departamento"], "15")
        self.assertEqual(normalized.loc[0, "codigo_municipio"], "15001")
        self.assertEqual(normalized.loc[0, "anio"], 2022)
        self.assertEqual(normalized.loc[0, "rendimiento_publicado_t_ha"], 20.0)

    def test_normalization_accepts_official_upra_headers(self):
        socrata = pd.DataFrame([eva_row()])
        reverse = {
            "c_digo_dane_departamento": "Código Dane departamento",
            "departamento": "Departamento",
            "c_digo_dane_municipio": "Código Dane municipio",
            "municipio": "Municipio",
            "cultivo": "Cultivo",
            "desagregaci_n_cultivo": "Desagregación cultivo",
            "a_o": "Año",
            "periodo": "Periodo",
            "rea_sembrada": "Área sembrada (ha)",
            "rea_cosechada": "Área cosechada (ha)",
            "producci_n": "Producción (t)",
            "rendimiento": "Rendimiento (t/ha)",
            "ciclo_del_cultivo": "Ciclo del cultivo",
            "estado_f_sico_del_cultivo": "Estado físico del cultivo",
        }
        normalized = normalize_eva(socrata.rename(columns=reverse))

        self.assertEqual(normalized.loc[0, "codigo_municipio"], "15001")
        self.assertEqual(normalized.loc[0, "rendimiento_publicado_t_ha"], 20.0)

    def test_raw_audit_flags_formula_and_duplicate_business_key(self):
        rows = [
            eva_row(),
            eva_row(production=210.0, yield_value=19.0),
        ]
        result = audit_raw_eva(pd.DataFrame(rows))

        self.assertEqual(result.summary.loc[0, "filas_en_llaves_duplicadas"], 2)
        self.assertEqual(result.summary.loc[0, "filas_rendimiento_formula_difiere"], 1)
        self.assertEqual(len(result.duplicate_keys), 1)

    def test_curation_recalculates_weighted_target(self):
        rows = [
            eva_row(harvested=10, production=200, yield_value=20),
            eva_row(
                disaggregation="Papa criolla",
                harvested=5,
                production=150,
                yield_value=30,
            ),
        ]
        result = curate_eva(pd.DataFrame(rows))

        self.assertEqual(len(result.curated), 1)
        self.assertAlmostEqual(result.curated.loc[0, "rendimiento_t_ha"], 350 / 15)
        self.assertEqual(result.curated.loc[0, "filas_fuente"], 2)
        self.assertTrue(result.exclusions.empty)

    def test_curation_excludes_incompatible_physical_states(self):
        rows = [
            eva_row(state="En fresco"),
            eva_row(disaggregation="Papa seca", state="Seco"),
        ]
        result = curate_eva(pd.DataFrame(rows))

        self.assertTrue(result.curated.empty)
        self.assertEqual(set(result.exclusions["motivo_exclusion"]), {"TAXONOMIA_INCOMPATIBLE"})

    def test_curated_audit_checks_unique_key_and_formula(self):
        curated = curate_eva(pd.DataFrame([eva_row()])).curated
        audit = audit_curated_eva(curated)

        self.assertEqual(audit["summary"].loc[0, "estado"], "COMPLETA")
        self.assertFalse(curated.duplicated(TARGET_KEY).any())


if __name__ == "__main__":
    unittest.main()
