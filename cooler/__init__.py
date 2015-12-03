#!/usr/bin/env python

import os
import re
import time
import json
import subprocess
from flask import Flask, render_template, request, redirect, url_for, jsonify
import RPi.GPIO as GPIO

DHT_PORT = 25
HUMIDIFIER_PORT = 23
AIRCON_PORT = 24

# GPIO mode init
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(HUMIDIFIER_PORT, GPIO.OUT)
GPIO.setup(AIRCON_PORT, GPIO.OUT)

app = Flask(__name__)
cur_dir = os.path.dirname(os.path.abspath(__file__))
dht = os.path.join(cur_dir, "../DHT/DHT")
setting_fname = os.path.join(cur_dir, "settings.json")


def get_dht(port):
    output = subprocess.check_output([dht, "2302", str(port)])
    time.sleep(2)

    matches = re.search("Temp =\s+([0-9.]+)", output)
    if not matches:
        return None, None
    temp = float(matches.group(1))

    matches = re.search("Hum =\s+([0-9.]+)", output)
    if not matches:
        return None, None
    humidity = float(matches.group(1))

    return temp, humidity


@app.route("/")
def index():
    settings = json.load(open(setting_fname))
    return render_template("index.html", settings=settings)


@app.route("/status")
def status():
    settings = json.load(open(setting_fname))
    temp, humidity = get_dht(DHT_PORT)
    return jsonify(humidifier=GPIO.input(HUMIDIFIER_PORT),
                   aircon=GPIO.input(AIRCON_PORT),
                   temp=temp,
                   humidity=humidity,
                   auto_mode=settings["auto_mode"])


@app.route("/switch", methods=["POST"])
def switch():
    """Accept POST request to toggle switches
    """
    item = request.form["item"]
    operation = request.form["operation"]
    if item not in ["humidifier", "aircon", "auto"] or operation not in ["on", "off"]:
        return jsonify(message="not supported item"), 400

    if item == "auto":
        settings = json.load(open(setting_fname))
        settings["auto_mode"] = True if operation == "on" else False
        json.dump(settings, open(setting_fname, 'w'))
        return jsonify(status="succeed")

    value = GPIO.HIGH if operation == "on" else GPIO.LOW
    if item == "humidifier":
        GPIO.output(HUMIDIFIER_PORT, value)
    elif item == "aircon":
        GPIO.output(AIRCON_PORT, value)

    return jsonify(status="succeed")


@app.route("/setting", methods=["GET", "POST"])
def setting():
    settings = json.load(open(setting_fname))
    if request.method == "GET":
        return render_template("setting.html", settings=settings)
    else:
        auto_mode = settings["auto_mode"]
        temp_min = request.form["temp_min"]
        temp_max = request.form["temp_max"]
        humi_min = request.form["humi_min"]
        humi_max = request.form["humi_max"]

        json.dump({"auto_mode": auto_mode,
                   "temp_min": temp_min,
                   "temp_max": temp_max,
                   "humi_min": humi_min,
                   "humi_max": humi_max}, open(setting_fname, 'w'))
        return redirect(url_for("index"))


@app.route("/cron")
def cron():
    """
    cron task, if we are in auto mode, check whether we need to toggle switch according to current temperature
    """
    settings = json.load(open(setting_fname))
    if settings["auto_mode"]:
        out = ""
        for attempt in range(7):
            temp, humidity = get_dht(DHT_PORT)
            if temp and humidity:
                break
        if temp is None or humidity is None:
            return "Cannot get current temperature, exiting."
        out += str(temp) + ',' + str(humidity)
        out += str(settings["temp_min"]) + "," + str(settings["temp_max"])
        out += "\ncurrent_status:" + str(GPIO.input(AIRCON_PORT)) + "\n"

        if temp < float(settings["temp_min"]) and GPIO.input(AIRCON_PORT) == 1:
            GPIO.output(AIRCON_PORT, GPIO.LOW)
            out += "aircon switch off"
        if temp > float(settings["temp_max"]) and GPIO.input(AIRCON_PORT) == 0:
            GPIO.output(AIRCON_PORT, GPIO.HIGH)
            out += "aircon switch on"

        if humidity < float(settings["humi_min"]) and GPIO.input(HUMIDIFIER_PORT) == 0:
            GPIO.output(HUMIDIFIER_PORT, GPIO.HIGH)
            out += "humidifier switch on"
        if humidity > float(settings["humi_max"]) and GPIO.input(HUMIDIFIER_PORT) == 1:
            GPIO.output(HUMIDIFIER_PORT, GPIO.LOW)
            out += "humidifier switch off"

        return out
    else:
        return "Not in auto mode"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=31415)
