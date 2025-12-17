from __future__ import annotations

from datetime import timedelta

DOMAIN = "stokercloud"

CONF_USERNAME = "username"

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=30)
DEFAULT_EVENT_UPDATE_INTERVAL = timedelta(minutes=5)

API_BASE = "https://stokercloud.dk/v2/dataout2"
LOGIN_PATH = "login.php"
CONTROLLER_DATA_PATH = "controllerdata2.php"
EVENT_DATA_PATH = "geteventdata.php"

TRANSLATION_BASE = "https://stokercloud.dk/v3/assets/json/translation"
DEFAULT_TRANSLATION_LANGUAGE = "uk"

DEFAULT_EVENT_COUNT = 100
DEFAULT_EVENT_OFFSET = 0

# Screen query captured from the web UI.
DEFAULT_SCREEN = (
    "b1,3,b2,5,b3,4,b4,6,b5,12,b6,14,b7,15,b8,16,b9,9,"
    "b10,0,"
    "d1,3,d2,4,d3,0,d4,0,d5,0,d6,0,d7,0,d8,0,d9,0,d10,0,"
    "h1,2,h2,3,h3,4,h4,7,h5,8,h6,0,h7,0,h8,0,h9,0,h10,0,"
    "w1,2,w2,3,w3,9,w4,0,w5,0"
)
