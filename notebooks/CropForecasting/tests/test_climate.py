import unittest

import numpy as np
import pandas as pd

from notebooks.CropForecasting.climate import (
    NASA_PARAMETERS,
    aggregate_asof_semester_indicators,
    build_asof_climate_scenario,
)


def synthetic_daily() -> pd.DataFrame:
    frames = []
    for year, value in ((2019, 10.0), (2020, 20.0), (2021, 30.0)):
        end = f"{year}-12-31" if year < 2021 else f"{year}-07-30"
        dates = pd.date_range(f"{year}-01-01", end, freq="D")
        frame = pd.DataFrame(
            {
                "codigo_departamento": "15",
                "codigo_municipio": "15001",
                "municipio_geografia": "TUNJA",
                "longitud": -73.3,
                "latitud": 5.5,
                "grid_longitud": -73.5,
                "grid_latitud": 5.5,
                "fecha": dates,
            }
        )
        for parameter in NASA_PARAMETERS:
            frame[parameter] = value
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


class ForecastClimateTest(unittest.TestCase):
    def test_scenario_keeps_observed_and_fills_future_with_prior_climatology(self):
        scenario = build_asof_climate_scenario(synthetic_daily(), 2021)
        observed = scenario[scenario["fecha"].eq(pd.Timestamp("2021-07-15"))].iloc[0]
        projected = scenario[scenario["fecha"].eq(pd.Timestamp("2021-08-15"))].iloc[0]

        self.assertEqual(observed["T2M"], 30.0)
        self.assertEqual(observed["origen_clima_dia"], "OBSERVADO")
        self.assertEqual(projected["T2M"], 15.0)
        self.assertEqual(projected["origen_clima_dia"], "CLIMATOLOGIA_HISTORICA")
        self.assertFalse(scenario[list(NASA_PARAMETERS)].isna().any().any())

    def test_semester_indicators_preserve_real_and_projected_day_counts(self):
        scenario = build_asof_climate_scenario(synthetic_daily(), 2021)
        indicators = aggregate_asof_semester_indicators(scenario)
        semester_a = indicators[indicators["tipo_periodo"].eq("A")].iloc[0]
        semester_b = indicators[indicators["tipo_periodo"].eq("B")].iloc[0]

        self.assertEqual(semester_a["dias_clima_climatologia"], 0)
        self.assertEqual(semester_a["tipo_escenario_climatico"], "OBSERVADO_COMPLETO")
        self.assertEqual(semester_b["dias_clima_real"], 30)
        self.assertEqual(semester_b["dias_clima_climatologia"], 154)
        self.assertTrue(np.isfinite(semester_b["precipitacion_total_mm"]))


if __name__ == "__main__":
    unittest.main()
