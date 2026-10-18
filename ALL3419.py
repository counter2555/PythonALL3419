"""Read temperature and humidity values from an ALLNET ALL3419 network sensor.

The device's web interface loads its values via AJAX requests that require a
request token (embedded in the start page), the session cookie and a current
unix timestamp. This module reproduces those requests.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from typing import Any

import requests
from bs4 import BeautifulSoup

__all__ = ["ALL3419", "ALL3419Error"]

DEFAULT_TIMEOUT = 10.0

# Form fields sent by the device's own web interface when polling the sensors.
_SENSOR_ARGUMENTS: dict[str, str] = {
    "q": "1",
    "elements[0][id]": "1",
    "elements[0][view]": "0",
    "elements[0][type]": "4",
    "elements[1][id]": "99",
    "elements[2][id]": "104",
    "elements[2][view]": "0",
    "elements[2][type]": "4",
    "elements[3][id]": "105",
    "elements[3][view]": "0",
    "elements[3][type]": "4",
    "elements[4][id]": "106",
    "elements[4][view]": "0",
    "elements[4][type]": "4",
    "elements[5][id]": "107",
    "elements[5][view]": "0",
    "elements[5][type]": "4",
    "device": "ALL3419",
}


class ALL3419Error(Exception):
    """Raised when the sensor cannot be reached or returns unexpected data."""


class ALL3419:
    """Client for an ALLNET ALL3419 temperature/humidity sensor.

    :param url: Base URL of the device, e.g. ``"http://192.168.0.10/"``.
    :param timeout: Timeout in seconds for every HTTP request.
    :param verify: TLS certificate verification, passed to ``requests``
        (``True``, ``False`` or a path to a CA bundle).
    :param session: Optional ``requests.Session`` to use.
    """

    def __init__(
        self,
        url: str,
        timeout: float = DEFAULT_TIMEOUT,
        verify: bool | str = True,
        session: requests.Session | None = None,
    ) -> None:
        if not url.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.verify = verify
        self.session = session or requests.Session()

    def __enter__(self) -> ALL3419:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self.session.close()

    @staticmethod
    def generate_arguments() -> dict[str, str]:
        """Return the form fields used to poll all sensors."""
        return dict(_SENSOR_ARGUMENTS)

    def get_data(self, path: str, arguments: Mapping[str, str] | None = None) -> str:
        """POST ``arguments`` to ``path`` on the device and return the response body.

        The request token, session cookie and timestamp are set automatically.
        """
        try:
            r = self.session.get(self.url + "/", timeout=self.timeout, verify=self.verify)
            r.raise_for_status()

            meta = BeautifulSoup(r.content, "html.parser").find("meta", {"name": "X-Request-Token"})
            token = meta.get("content") if meta is not None else None
            if not token:
                raise ALL3419Error("X-Request-Token not found on start page")

            args = dict(arguments) if arguments is not None else self.generate_arguments()
            args["ts"] = str(round(time.time()))

            r = self.session.post(
                self.url + "/" + path.lstrip("/"),
                data=args,
                headers={"X-Request-Token": str(token), "X-Requested-With": "XMLHttpRequest"},
                timeout=self.timeout,
                verify=self.verify,
            )
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            raise ALL3419Error(f"Request to {self.url} failed: {e}") from e

    def get_name_number_pairs(self) -> dict[str, str]:
        """Return a mapping of sensor id to sensor name."""
        data = self.get_data("/sensorpanel.php", arguments={"gw": "0", "site": "sensorpanel"})
        soup = BeautifulSoup(data, "html.parser")

        pairs: dict[str, str] = {}
        for f in soup.find_all("div", {"class": "sensor_message"}):
            name, element_id, unit = f.get("name"), f.get("id"), f.get("unit")
            if not (name and element_id and unit):
                continue
            sensor_id = str(element_id).split("_")[-1]
            pairs[sensor_id] = str(name) if unit == "°C" else f"{name} Humidity"
        return pairs

    def get_temperature(self) -> dict[str, float]:
        """Return all values as a dict mapping sensor name to temperature / humidity."""
        text = self.get_data("/ajax/read_sensors.php")
        try:
            data: dict[str, Any] = json.loads(text)
        except json.JSONDecodeError as e:
            raise ALL3419Error(f"Invalid JSON from sensor: {e}") from e
        if not isinstance(data, dict):
            raise ALL3419Error("Unexpected sensor response format")

        pairs = self.get_name_number_pairs()

        results: dict[str, float] = {}
        for sensor_id, name in pairs.items():
            entry = data.get(sensor_id)
            if not isinstance(entry, dict) or "value" not in entry:
                continue
            try:
                results[name] = float(entry["value"])
            except (TypeError, ValueError):
                continue
        return results

    # Backwards-compatible names
    GenerateArguments = generate_arguments
    GetData = get_data
    GetNameNumberPairs = get_name_number_pairs
    GetTemperature = get_temperature


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} http://address/")
    with ALL3419(sys.argv[1]) as sensor:
        print(sensor.get_temperature())
