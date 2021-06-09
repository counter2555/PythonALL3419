import requests
import time
import numpy as np
from bs4 import BeautifulSoup
import json

#---------------------------------------------------------
# Reads temperature and humidity values from AllNet AL3419
#---------------------------------------------------------
class ALL3419:
    def __init__(self, url):
        self.url = url

    #Recreates arguments from HTTP Post (ajax)
    def GenerateArguments(self):
        enc = "q=1&elements[0][id]=1&elements[0][view]=0&elements[0][type]=4&elements[1][id]=99&elements[2][id]=104&elements[2][view]=0&elements[2][type]=4&elements[3][id]=105&elements[3][view]=0&elements[3][type]=4&elements[4][id]=106&elements[4][view]=0&elements[4][type]=4&elements[5][id]=107&elements[5][view]=0&elements[5][type]=4&device=ALL3419"
        vs = enc.split("&")

        arguments = {}

        for e in vs:
            s = e.split("=")
            arguments[s[0]] = s[1]

        arguments["ts"] = str(int(np.round(time.time())))

        return arguments

    #Returns data from given php file
    #Note that a validation token, a cookie and a correct unix timestamp have to be set (done here automatically)
    def GetData(self, path, arguments=None):
        try:
            session = requests.Session()

            r = requests.get(self.url)
            doc = BeautifulSoup(r.content, "html.parser")
            token = doc.find("meta", {"name" : "X-Request-Token"})["content"]

            cookies = dict(r.cookies)
            headers = {"X-Request-Token": token, "X-Requested-With": "XMLHttpRequest"}

            if(arguments == None):
                args = self.GenerateArguments()
            else:
                args = arguments
                args["ts"] = str(int(np.round(time.time())))

            r = requests.post(self.url + path, data=args, cookies=cookies, headers=headers)

            return r.text
        except Exception as e:
            print(e)
            return -1

    #Returns pairs of id-numbers and their corresponding values
    def GetNameNumberPairs(self):
        data = self.GetData("/sensorpanel.php", arguments={"gw":"0", "site":"sensorpanel"})
        soup = BeautifulSoup(data, "html.parser")
        finds = soup.find_all("div", {"class" : "sensor_message"})

        pairs = {}

        for f in finds:
            try:
                name = f["name"]
                id = f["id"].split("_")[-1]
                unit = f["unit"]

                if unit == "°C":
                    pairs[id] = name
                else:
                    pairs[id] = name+" Humidity"
            except:
                pass
        return pairs

    #returns all temperatures as dictionary, where the index is the name of the sensor and the value is the temperature / humidity
    def GetTemperature(self):
        try:
            text = self.GetData("/ajax/read_sensors.php")
            data = json.loads(text)

            pairs = self.GetNameNumberPairs()

            results = {}
            for k in data.keys():
                if k in pairs.keys():
                    results[pairs[k]] = float(data[k]["value"])

            return results

        except Exception as e:
            print(e)
            return -1


if __name__ == "__main__":
    tc = ALL3419("http://address/")
    print(tc.GetTemperature())