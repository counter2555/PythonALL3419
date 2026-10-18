import pytest
import requests
import responses

from ALL3419 import ALL3419, ALL3419Error

BASE = "http://sensor.local"
START_PAGE = '<html><head><meta name="X-Request-Token" content="abc123"></head></html>'
PANEL = """
<div class="sensor_message" name="Office" id="sensor_104" unit="°C"></div>
<div class="sensor_message" name="Office" id="sensor_105" unit="%"></div>
<div class="sensor_message" id="sensor_106"></div>
"""
READINGS = '{"104": {"value": "21.5"}, "105": {"value": "40"}, "999": {"value": "1"}}'


def _mock_device(rsps, readings=READINGS):
    rsps.get(BASE + "/", body=START_PAGE, headers={"Set-Cookie": "sid=xyz"})
    rsps.post(BASE + "/sensorpanel.php", body=PANEL)
    rsps.post(BASE + "/ajax/read_sensors.php", body=readings)


@responses.activate
def test_get_temperature():
    _mock_device(responses)
    assert ALL3419(BASE + "/").get_temperature() == {"Office": 21.5, "Office Humidity": 40.0}

    post = responses.calls[1].request
    assert post.headers["X-Request-Token"] == "abc123"
    assert post.headers["X-Requested-With"] == "XMLHttpRequest"
    assert "sid=xyz" in post.headers["Cookie"]
    assert "ts=" in post.body


@responses.activate
def test_legacy_names():
    _mock_device(responses)
    assert ALL3419(BASE).GetTemperature()["Office"] == 21.5


@responses.activate
def test_arguments_not_mutated():
    _mock_device(responses)
    args = {"gw": "0"}
    ALL3419(BASE).get_data("/sensorpanel.php", args)
    assert args == {"gw": "0"}


@responses.activate
def test_missing_token():
    responses.get(BASE + "/", body="<html></html>")
    with pytest.raises(ALL3419Error):
        ALL3419(BASE).get_temperature()


@responses.activate
def test_invalid_json():
    _mock_device(responses, readings="not json")
    with pytest.raises(ALL3419Error):
        ALL3419(BASE).get_temperature()


@responses.activate
def test_connection_error():
    responses.get(BASE + "/", body=requests.ConnectionError("down"))
    with pytest.raises(ALL3419Error):
        ALL3419(BASE).get_temperature()


def test_rejects_non_http_url():
    with pytest.raises(ValueError):
        ALL3419("file:///etc/passwd")
