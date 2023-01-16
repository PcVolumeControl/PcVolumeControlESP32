"""
This file can be copied into the esp with:

ampy --port /dev/tty.usbserial-120 main.py /main.py

That will place the file in a place where it will be executed on boot.

The initial starting state of the ESP32 is going to be a missing /SETUP file.
When this file does not exist, the system goes into AP mode so you can connect
to it and tell it what your home network ssid/password is. When that's entered,
it should restart and try to connect to the provided ssid. 

When this connects to wifi, it will start the webREPL so you
can connect to it in a browser. This is going to come up at http://<address>:8266
This is useful for looking at the actual micropython console output.

The simple webserver this starts in AP mode (to get your ssid/pwd) remains up at
http://<address> in case you need to change the network settings. 
These settings are stored in that /SETUP file on the local filesystem.

BONUS: Unlike the serial port connections which must only have one connection
at a time, you can have the webREPL open as you connect via serial elsewhere.
This is good if you want to tail logs or see program output.
"""

import os
import socket
import sys
import time

import machine
from machine import Pin
import network

AP_SSID = "pcvc"
AP_PASS = "pcvc"
AP_MODE = True
DEFAULTS_FILE = "SETUP"

# This is meant to show when wifi is actively on and connected.
# connect pin 13 to a 220ohm resistor and LED to make this work.
WIFI_STATUS_PIN = Pin(13, Pin.OUT)


def ap_setup_mode():
    """
    This is used when the ESP32 first boots. This puts
    the antenna in AP mode for the initial wifi setup step.
    """
    wlan = network.WLAN(network.AP_IF)
    wlan.config(essid=AP_SSID, password=AP_PASS)
    wlan.active(True)
    return wlan


def connect_to_ssid():
    """
    When a /SETUP file exists on disk, this connects to
    the ssid listed in that file using the password from the file.

    If it cannot connect to the wifi network, it resets after 30 seconds,
    starting back up in AP mode.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)

    wlan.active(True)
    if not wlan.isconnected():
        print("connecting to network...")
        with open(DEFAULTS_FILE) as f:
            data = f.read().splitlines()
            try:
                ssid, password = data[0], data[1]
            except:  # bad data
                raise RuntimeError("wifi ssid and/or password not present in config")
        wlan.connect(ssid, password)
        # Give up with an exception after 30 seconds.
        tries = 30
        while not wlan.isconnected():
            if tries == 0:
                raise RuntimeError("wifi connection unsuccessful")
            else:
                print("attempting to connect to SSID '%s'" % ssid)
                tries -= 1
                time.sleep(1)
    print("connection established")
    print("network config:", wlan.ifconfig())
    return wlan


def process_post(data):
    """
    Take HTTP POST request data (headers+data) and return a dict of {ssid: password}

    The incoming request looks like this.
    GET/POST/WHATEVS
    header: value
    header: value
    ...more headers...

    ssid=somename&passwd=somepwd

    The header-data boundary is always a blank line.
    """
    ret = {}
    header_boundary = False
    for line in data.splitlines():
        if not line:
            # Between the headers and data there is a blank line
            header_boundary = True
            continue
        if header_boundary:
            # Everything after that blank line is expected to be data
            try:
                parts = line.split("&")
                for part in parts:
                    p = part.split("=")
                    # doing this for input sanitization.
                    if p[0] == "ssid":
                        ret["ssid"] = p[1]
                    elif p[0] == "passwd":
                        ret["passwd"] = p[1]
            except:
                pass  # request payload malformed, go away

    return ret


def run_webserver():
    """
    This simple webserver supports GET and POST requests. It's
    used on the initial configuration step to provide a web form
    for wifi ssid/password to be entered.

    If new wifi information is posted using this form, the esp will
    reboot itself from this function. Upon reboot, it should attempt a
    connection to that network.

    The webserver can be used eventually to display information on the streams
    or the volume levels it sees. Or maybe some more settings.
    """
    reset_needed = False
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", 80))
    except OSError:
        pass  # IP/port already bound, great.
    s.listen(5)

    # The html form sent in response to a GET request
    with open("configure.html") as f:
        html = f.read()

    while True:
        conn, addr = s.accept()
        print("Got a connection from %s" % str(addr))
        request = conn.recv(1024)
        request = request.decode("utf-8")
        for line in request.splitlines():
            print(line)

        response = "you shouldn't see this...if so it's a boog"

        if request.startswith("GET "):
            response = html
            conn.send("HTTP/1.1 200 OK\n")
        elif request.startswith("POST "):
            p = process_post(request)
            if "passwd" in p and "ssid" in p:
                print("valid POST received, setting defaults...")
                with open(DEFAULTS_FILE, "w") as f:
                    f.write(p["ssid"])
                    f.write("\n")
                    f.write(p["passwd"])
                print("done setting defaults")

            response = "setup complete, rebooting in 10 seconds to connect to this access point..."
            conn.send("HTTP/1.1 201 CREATED\n")
            reset_needed = True
        if response:
            conn.send("Content-Type: text/html\n")
            conn.send("Connection: close\n\n")

        conn.sendall(response)
        conn.close()
        # wait a bit so they can read the page before it resets
        if reset_needed:
            time.sleep(10)
            machine.reset()


def main(startup_mode):
    """
    The idea is initial boot it starts in AP mode.
    That gives you the chance to connect and tell it the ssid/password
    for your real home network.
    That information gets written to disk on the ESP.
    Presence of that file means the ESP has your network config and will now
    use the contents of that file to connect to your wifi network.
    """

    if startup_mode:
        print(
            "starting in setup/AP mode. Connect to SSID '%s' Open http://192.168.4.1 in a browser to configure wifi."
            % AP_SSID
        )
        wl = ap_setup_mode()
    else:
        print("starting and connecting to configured wifi network...")
        try:
            wl = connect_to_ssid()
        except RuntimeError:
            print("wifi connection failure, soft rebooting")
            os.remove(DEFAULTS_FILE)
            machine.reset()

    if wl.isconnected():
        WIFI_STATUS_PIN.value(1)

    run_webserver()


if __name__ == "__main__":
    try:
        open(DEFAULTS_FILE).close()
        AP_MODE = False
    except OSError:
        pass  # file not found, go into AP Mode
    main(AP_MODE)
