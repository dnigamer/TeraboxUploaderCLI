import os
import json
import re

#### TERABOX AUTHENTICATION ####
if not os.path.exists("secrets.json"):
    print("!! Error: secrets.json file not found.")
    exit()

with open("secrets.json", "r") as f:
    secrets = json.load(f)
    jstoken = secrets["jstoken"]
    bdstoken = secrets["bdstoken"]
    cookies = secrets["cookies"]

#### PROGRAM CONFIGURATIONS ####
# local directory to upload files from
sourceloc = "/Users/goncalo/Documents/teraboxturboshit/upload"
remoteloc = "/uploadmac"  # remote directory to upload files

movefiles = False  # move files to another directory after upload
# directory to move files to if movefiles is True
movetoloc = "/Users/goncalo/Documents/teraboxturboshit/uploaded"

downshare = True  # show share link after upload
expirdate = 0  # expiration date for share link (0 = never)
delsrcfil = False  # delete source file after upload

#### PROGRAM INTERNAL VARS ####
useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
useragent += "(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
baseurltb = "https://www.terabox.com"

if not os.path.exists(sourceloc) and not os.path.isdir(sourceloc):
    print("!! ERROR: Source directory does not exist. Please check the path.")
    exit()

if not os.path.exists(movetoloc) and not os.path.isdir(movetoloc) and movefiles:
    print("!! ERROR: Move to directory does not exist. Please check the path.")
    exit()

if not (any(char.isdigit() for char in jstoken) and any(char.isdigit() for char in bdstoken)):
    print("!! ERROR: Invalid token.")
    exit()

# Delete files matching the pattern "*piece[0-9]*" in the temp directory
if os.path.exists(f"{sourceloc}/temp"):
    print("ii INFO: Cleaning up temp directory...")
    for filename in os.listdir(f"{sourceloc}/temp"):
        if re.search(r"\d+piece", filename):
            os.remove(os.path.join(sourceloc, filename))
    print("ii INFO: Temp directory cleared.")
else:
    print("ii INFO: Creating temp directory...")
    os.mkdir(f"{sourceloc}/temp")
    print("ii INFO: Temp directory created.")
