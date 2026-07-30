from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from notebooks.CropForecasting.climate import NASA_PARAMETERS, _request_power
from notebooks.CropForecasting.run_pipeline import download_eva_if_missing


class FakeResponse:
    def __init__(self, *, chunks=(), payload=None):
        self.chunks = chunks
        self.payload = payload
        self.status_checked = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def raise_for_status(self):
        self.status_checked = True

    def iter_content(self, *, chunk_size):
        self.chunk_size = chunk_size
        yield from self.chunks

    def json(self):
        return self.payload


class NetworkSecurityTest(unittest.TestCase):
    def test_eva_download_verifies_tls_and_validates_response(self):
        calls = []
        response = FakeResponse(chunks=(b"x" * 1_000_001,))

        def request_get(url, **kwargs):
            calls.append((url, kwargs))
            return response

        with TemporaryDirectory() as directory:
            target = Path(directory) / "eva.xlsx"
            result = download_eva_if_missing(target, request_get=request_get)
            self.assertEqual(result, target)
            self.assertEqual(target.stat().st_size, 1_000_001)

        self.assertTrue(response.status_checked)
        self.assertTrue(calls[0][1]["verify"])
        self.assertTrue(calls[0][1]["stream"])
        self.assertEqual(calls[0][1]["timeout"], (10, 180))

    def test_incomplete_eva_download_is_removed(self):
        response = FakeResponse(chunks=(b"incomplete",))

        with TemporaryDirectory() as directory:
            target = Path(directory) / "eva.xlsx"
            with self.assertRaisesRegex(ValueError, "menor o igual a 1 MB"):
                download_eva_if_missing(
                    target,
                    request_get=lambda *args, **kwargs: response,
                )
            self.assertFalse(target.exists())
            self.assertFalse(target.with_suffix(".xlsx.tmp").exists())

    def test_power_request_verifies_tls_and_validates_response(self):
        calls = []
        parameters = {parameter: {"20260101": 1.0} for parameter in NASA_PARAMETERS}
        response = FakeResponse(payload={"properties": {"parameter": parameters}})

        def request_get(url, **kwargs):
            calls.append((url, kwargs))
            return response

        result = _request_power(
            5.5,
            -73.5,
            start="20260101",
            end="20260101",
            request_get=request_get,
        )

        self.assertEqual(result["properties"]["parameter"], parameters)
        self.assertTrue(response.status_checked)
        self.assertTrue(calls[0][1]["verify"])
        self.assertEqual(calls[0][1]["timeout"], (10, 120))


if __name__ == "__main__":
    unittest.main()
