'''
ISS Tracker Demo for the Interstate 75 W
Uses one 128 x 64 Matrix panel.

You will need to transfer the 'worldmap.py' file to your I75W
and have a secrets.py with your network details filled in.

'''

import time
from interstate75 import Interstate75, DISPLAY_INTERSTATE75_128X64
from picovector import PicoVector, Polygon, Transform
import requests
from ezwifi import EzWiFi
import asyncio
import math
from micropython import const
from worldmap import PATHS

API_URL = 'http://api.open-notify.org/iss-now.json'
INTERVAL = const(5)

R = const(6378137)
MAP_WIDTH = const(128)
MAP_HEIGHT = const(64)
OFFSET_X = const(5)
OFFSET_Y = const(9)

PI = math.pi

# Store the last good lat and long values to fall back on.
last_lat = 0
last_long = 0

# Setup for the display
i75 = Interstate75(
    display=DISPLAY_INTERSTATE75_128X64, stb_invert=False, panel_type=Interstate75.PANEL_GENERIC)
display = i75.display

# Pico Vector
vector = PicoVector(display)

t = Transform()
vector.set_transform(t)

# Pens
GREEN = display.create_pen(0, 255, 0)
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)

WIDTH, HEIGHT = display.get_bounds()


# handler for network callbacks
def log_handler(wifi, message):
    print(message)


# Get the current location data for the ISS
def get_location():
    try:
        req = requests.get(API_URL, timeout=None)
        json = req.json()

        lat = float(json['iss_position']['latitude'])
        long = float(json['iss_position']['longitude'])

        return lat, long

    except OSError:
        print("Error getting ISS data. Skipping update.")


# Convert the location data to X and Y coordinates
# Reference:
# https://stackoverflow.com/questions/14329691/convert-latitude-longitude-point-to-a-pixels-x-y-on-mercator-projection
def convert(latitude, longitude):
    # get x value
    x = (longitude + 180) * (MAP_WIDTH / 360)

    # convert from degrees to radians
    latRad = (latitude * PI) / 180

    # get y value
    mercN = math.log(math.tan((PI / 4) + (latRad / 2)))
    y = (MAP_HEIGHT / 2) - (MAP_WIDTH * mercN / (2 * PI))

    if x >= OFFSET_X:
        x -= OFFSET_X

    return int(x), int(y + OFFSET_Y)


# Clear the display and show a loading msg
display.set_pen(BLACK)
display.clear()
display.set_pen(WHITE)
display.text("LOADING...", 5, 32, WIDTH, 1)
i75.update()

# Setup EZWiFi and start connection process
network = EzWiFi(info=log_handler, warning=log_handler, error=log_handler)
asyncio.get_event_loop().run_until_complete(network.connect())

# Wait for a connection before continuing.
while not network.isconnected():
    pass

# Assemble our world map vector
world = Polygon()

for shape in PATHS:
    world.path(*shape)

t.translate(-5, -33)
t.scale(1.0, 0.93)

while True:

    # Get our lat and long values, we'll capture any exceptions here too
    # returning the previous good values in those instances
    try:
        lat, long = get_location()
        last_lat = lat
        last_long = long
    except Exception:
        lat = last_lat
        long = last_long

    # and convert those values to X and Y coords
    x, y = convert(lat, long)

    # Clear the screen
    display.set_pen(BLACK)
    display.clear()

    # Draw our world map vector
    display.set_pen(WHITE)
    vector.draw(world)

    # Draw our marker for the ISS
    display.set_pen(GREEN)
    display.circle(x, y, 1)

    # Update the display and wait.
    i75.update()
    time.sleep(INTERVAL)
