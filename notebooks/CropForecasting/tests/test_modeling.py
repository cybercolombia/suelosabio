import unittest

import pandas as pd

from notebooks.CropForecasting.modeling import (
    PersistenceRegressor,
    regression_metrics,
)


class ForecastModelingTest(unittest.TestCase):
    def test_standard_metrics_are_exact_for_perfect_prediction(self):
        metrics = regression_metrics([10.0, 20.0, 30.0], [10.0, 20.0, 30.0])

        self.assertEqual(metrics["n"], 3)
        self.assertAlmostEqual(metrics["mae"], 0.0)
        self.assertAlmostEqual(metrics["rmse"], 0.0)
        self.assertAlmostEqual(metrics["r2"], 1.0)
        self.assertAlmostEqual(metrics["smape_pct"], 0.0)

    def test_persistence_regressor_is_fitted_and_serializable_in_shape(self):
        features = pd.DataFrame(
            {
                "rendimiento_lag_1": [10.0, 20.0],
                "rendimiento_media_historica": [9.0, 18.0],
            }
        )
        estimator = PersistenceRegressor("lag_1").fit(features, [11.0, 21.0])

        self.assertEqual(estimator.predict(features).tolist(), [10.0, 20.0])
        self.assertEqual(estimator.training_median_, 16.0)


if __name__ == "__main__":
    unittest.main()
