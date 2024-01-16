import os
import json
import re

# TERABOX AUTHENTICATION
if not os.path.exists("secrets.json"):
    print("!! ERROR: secrets.json file not found.")
    print("!! ERROR: Please create a secrets.json file with the following format:")
    print("{")
    print('    "jstoken": "your jstoken token",')
    print('    "bdstoken": "your bdstoken token",')
    print('    "cookies": {')
    print('        "csrfToken": "your csrfToken token",')
    print('        "browserid": "your browserid",')
    print('        "lang": "your lang (NOT REQUIRED)",')
    print('        "ndus": "your ndus token",')
    print('        "ndut_fmt": "your ndut_fmt token",')
    print('    }')
    print("}")
    exit()

with open("secrets.json", "r") as f:
    secrets = json.load(f)
    jstoken = secrets["jstoken"]
    bdstoken = secrets["bdstoken"]
    cookies = secrets["cookies"]
    f.close()

if not (any(char.isdigit() for char in jstoken) and any(char.isdigit() for char in bdstoken)):
    print("!! ERROR: Invalid token.")
    exit()

print("ii INFO: Loaded secrets.")

# PROGRAM CONFIGURATION
if not os.path.exists("settings.json"):
    print("!! Error: secrets.json file not found.")
    exit()

with open("settings.json", "r") as f:
    settings = json.load(f)
    sourceloc = settings["directories"]["sourcedir"]
    remoteloc = settings["directories"]["remotedir"]
    movetoloc = settings["directories"]["uploadeddir"]
    movefiles = True if settings["settings"]["movefiles"] == "true" else False
    downshare = True if settings["settings"]["sharelink"] == "true" else False
    expirdate = settings["settings"]["expireshare"]
    delsrcfil = True if settings["settings"]["deletesource"] == "true" else False
    f.close()

if not sourceloc or not remoteloc or not movetoloc:
    print("!! ERROR: Invalid directory paths.")
    exit()

if not os.path.exists(sourceloc) and not os.path.isdir(sourceloc):
    print("!! ERROR: Source directory does not exist. Please check the path.")
    exit()

if not os.path.exists(movetoloc) and not os.path.isdir(movetoloc) and movefiles:
    print("!! ERROR: Move to directory does not exist. Please check the path.")
    exit()

print("ii INFO: Loaded settings.")

#### PROGRAM INTERNAL VARS ####
useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
useragent += "(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
baseurltb = "https://www.terabox.com"

# Delete files matching the pattern "*piece[0-9]*" in the temp directory
if os.path.exists(f"{sourceloc}/temp"):
    print("ii INFO: Cleaning up temp directory...")
    for filename in os.listdir(f"{sourceloc}/temp"):
        if re.search(r"piece+\d", filename):
            os.remove(os.path.join(sourceloc, filename))
    print("ii INFO: Temp directory cleared.")
else:
    print("ii INFO: Creating temp directory...")
    os.mkdir(f"{sourceloc}/temp")
    print("ii INFO: Temp directory created.")
