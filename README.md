# PythonALL3419
Python module for reading the temperature values from an ALLNET ALL3419 network temperature sensor. The temperature values are read by using HTTP POST.

Usage:

```python
from ALL3419 import ALL3419

sensor = ALL3419("http://address/")

#GetTemperature() returns a dictionary, where the keys are the sensor names
data = sensor.GetTemperature()
```
