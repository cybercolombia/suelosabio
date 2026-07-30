import unittest

import pandas as pd

from notebooks.CropForecasting.dataset import add_history_features
from notebooks.CropForecasting.eva import select_target_municipalities


class ForecastDatasetTest(unittest.TestCase):
    def test_history_features_never_use_current_or_future_target(self):
        data = pd.DataFrame(
            {
                "codigo_municipio": ["15001"] * 4,
                "tipo_periodo": ["A"] * 4,
                "anio": [2022, 2023, 2024, 2025],
                "rendimiento_t_ha": [10.0, 20.0, 30.0, 999.0],
                "area_sembrada_ha": [100.0, 110.0, 120.0, 9999.0],
            }
        )
        featured = add_history_features(data)
        row_2025 = featured[featured["anio"].eq(2025)].iloc[0]

        self.assertEqual(row_2025["rendimiento_lag_1"], 30.0)
        self.assertEqual(row_2025["rendimiento_lag_2"], 20.0)
        self.assertEqual(row_2025["rendimiento_media_historica"], 20.0)
        self.assertEqual(row_2025["area_sembrada_lag_1"], 120.0)

    def test_top_municipalities_use_only_2024_2025_area(self):
        rows = []
        for department in ("15", "25"):
            for municipality_index in range(12):
                code = f"{department}{municipality_index + 1:03d}"
                for year in (2024, 2025):
                    for period in ("A", "B"):
                        rows.append(
                            {
                                "codigo_departamento": department,
                                "departamento": (
                                    "Boyacá" if department == "15" else "Cundinamarca"
                                ),
                                "codigo_municipio": code,
                                "municipio": f"M{municipality_index:02d}",
                                "anio": year,
                                "tipo_periodo": period,
                                "area_sembrada_ha": float(12 - municipality_index),
                                "rendimiento_t_ha": 20.0,
                            }
                        )
        potato = pd.DataFrame(rows)
        selected = select_target_municipalities(potato)

        self.assertEqual(len(selected), 20)
        self.assertEqual(
            selected.groupby("codigo_departamento").size().to_dict(),
            {"15": 10, "25": 10},
        )
        self.assertNotIn("15012", set(selected["codigo_municipio"]))
        self.assertEqual(
            set(selected["anios_seleccion"]), {"2024,2025"}
        )

    def test_selection_rejects_forecast_year(self):
        with self.assertRaisesRegex(ValueError, "anteriores"):
            select_target_municipalities(pd.DataFrame(), years=(2025, 2026))


if __name__ == "__main__":
    unittest.main()
