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

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(HUMIDIFIER_PORT, GPIO.OUT)
# air conditioner
GPIO.setup(AIRCON_PORT, GPIO.OUT)

#GPIO.output(LIGHT_PORT, GPIO.LOW)
#GPIO.output(AIRCON_PORT, GPIO.LOW)
# the DHT
#GPIO.setup(25, GPIO.IN)
 
app = Flask(__name__)
cur_dir = os.path.dirname(os.path.abspath(__file__))
dht = os.path.join(cur_dir, "DHT/DHT")
setting_fname = os.path.join(cur_dir, "settings.json")

from functools import wraps
from flask import request, Response

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'pi' and password == 'loveLYU'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        #if request.remote_addr
        return request.remote_addr
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

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
    
@requires_auth
@app.route("/")
def index():
    settings = json.load(open(setting_fname))
    return render_template("index.html", settings=settings)

@requires_auth
@app.route("/status")
def status():
    settings = json.load(open(setting_fname))
    temp, humidity = get_dht(DHT_PORT)
    #temp, humidity = 0,1
    return jsonify(humidifier=GPIO.input(HUMIDIFIER_PORT), 
                   aircon=GPIO.input(AIRCON_PORT),
                   temp=temp,
                   humidity=humidity,
                   auto_mode=settings["auto_mode"])

@requires_auth
@app.route("/switch", methods=["POST"])
def switch():
    if request.method != "POST":
        return jsonify(status="fail", error="not supported method")

    item = request.form["item"]
    operation = request.form["operation"]
    if item not in ["humidifier", "aircon", "auto"]:
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
    if item == "humidifier":
        GPIO.output(HUMIDIFIER_PORT, value)
    elif item == "aircon":
        GPIO.output(AIRCON_PORT, value)

    #time.sleep(1)
    #unlock
    #os.remove(lock_fname)

    return jsonify(status="succeed")

@requires_auth
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
    settings = json.load(open(setting_fname))
    if settings["auto_mode"]:
        out = ""
        max_attemp = 7
        while (max_attemp > 0):
            max_attemp -= 1
            temp, humidity = get_dht(DHT_PORT)
            if temp and humidity:
                break
        if max_attemp == 0:
            return "Cannot get corrent temp this time."
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
