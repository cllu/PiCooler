#!/usr/bin/env python

import os
import re
import time
import json
import subprocess 
from flask import Flask, render_template, request, redirect, url_for, jsonify
import RPi.GPIO as GPIO

DHT_PORT = 25
LIGHT_PORT = 23
AIRCON_PORT = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
# the light
GPIO.setup(LIGHT_PORT, GPIO.OUT)
# air conditioner
GPIO.setup(AIRCON_PORT, GPIO.OUT)

GPIO.output(LIGHT_PORT, GPIO.LOW)
GPIO.output(AIRCON_PORT, GPIO.LOW)
# the DHT
#GPIO.setup(25, GPIO.IN)
 
app = Flask(__name__)
cur_dir = os.path.dirname(os.path.abspath(__file__))
dht = os.path.join(cur_dir, "DHT/DHT")
setting_fname = os.path.join(cur_dir, "settings.json")

def get_dht(port):
    output = subprocess.check_output([dht, "2302", str(port)])
    time.sleep(2)

    matches = re.search("Temp =\s+([0-9.]+)", output)
    if (not matches):
        return None, None
    temp = float(matches.group(1))

    matches = re.search("Hum =\s+([0-9.]+)", output)
    if (not matches):
        return None, None
    humidity = float(matches.group(1))

    return temp, humidity
    
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    settings = json.load(open(setting_fname))
    temp, humidity = get_dht(DHT_PORT)
    #temp, humidity = 0,1
    return jsonify(light=GPIO.input(LIGHT_PORT), 
                   aircon=GPIO.input(AIRCON_PORT),
                   temp=temp,
                   humidity=humidity,
                   auto_mode=settings["auto_mode"])

@app.route("/switch", methods=["POST"])
def switch():
    if request.method != "POST":
        return jsonify(status="fail", error="not supported method")

    item = request.form["item"]
    operation = request.form["operation"]
    if item not in ["light", "aircon", "auto"]:
        return jsonify(status="fail", error="not supported item")
    if operation not in ["on", "off"]:
        return jsonify(status="fail", error="not supported operation")

    if item == "auto":
        settings = json.load(open(setting_fname))
        settings["auto_mode"] = True if operation == "on" else False
        json.dump(settings, open(setting_fname, 'w'))
        return jsonify(status="succeed")

    #lock_fname = os.path.join("/tmp", item+".lock") 
    #if os.path.isfile(lock_fname):
    #    return jsonify(status="fail", error="wait for a moment")

    #lock the operation
    #open(lock_fname, 'a').close()
    value = GPIO.HIGH if operation == "on" else GPIO.LOW
    if item == "light":
        GPIO.output(LIGHT_PORT, value)
    elif item == "aircon":
        GPIO.output(AIRCON_PORT, value)

    #time.sleep(1)
    #unlock
    #os.remove(lock_fname)

    return jsonify(status="succeed")


@app.route("/setting", methods=["GET", "POST"])
def setting():
    settings = json.load(open(setting_fname))
    if request.method == "GET":
        return render_template("setting.html", settings=settings)
    else:
        auto_mode = settings["auto_mode"]
        #if "auto_mode" in request.form:
        #    auto_mode = True
        temp_min = request.form["temp_min"]
        temp_max = request.form["temp_max"]

        json.dump({"auto_mode:": auto_mode,
                   "temp_min": temp_min,
                   "temp_max": temp_max}, open(setting_fname, 'w'))
        return "Done"

@app.route("/cron")
def cron():
    settings = json.load(open(setting_fname))
    if settings["auto_mode"]:
        temp, humidity = get_dht(DHT_PORT)
        if temp < settings["temp_min"] and GPIO.input(AIRCON_PORT):
            GPIO.output(AIRCON_PORT, GPIO.LOW)
        if temp > settings["temp_max"] and not GPIO.input(AIRCON_PORT):
            GPIO.output(AIRCON_PORT, GPIO.HIGH)

    return "Done"

if __name__ == "__main__":
   
    app.run(host="0.0.0.0")
