# PythonALL3419

Python module for reading the temperature and humidity values from an ALLNET ALL3419
network temperature sensor. The values are read via the same HTTP POST (AJAX) requests the
device's web interface uses.

Requires Python 3.11+.

## Installation

```bash
poetry install
# or
pip install .
```

## Usage

```python
from ALL3419 import ALL3419, ALL3419Error

with ALL3419("http://address/", timeout=10) as sensor:
    try:
        # Dictionary mapping sensor names to temperature / humidity values
        data = sensor.get_temperature()
    except ALL3419Error as e:
        print(f"Could not read sensor: {e}")
```

Or from the command line:

```bash
poetry run python ALL3419.py http://address/
```

### Changes in 1.0

- Errors raise `ALL3419Error` instead of printing and returning `-1`.
- Methods use snake_case (`get_temperature`, `get_data`, ...). The old CamelCase names
  (`GetTemperature`, ...) still work.
- All requests have a timeout (default 10 s) and fail on HTTP error status codes.
- `numpy` is no longer required.

### Security note

The ALL3419 web interface is usually served over plain HTTP, so the request token and session
cookie travel unencrypted. Only use it on a trusted network. If your device supports HTTPS, use
an `https://` URL; pass `verify="/path/to/ca.pem"` for a self-signed certificate rather than
disabling verification.

## Development

```bash
poetry install
poetry run pytest
poetry run ruff check .
poetry run ruff format .
```
