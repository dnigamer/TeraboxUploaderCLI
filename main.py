import glob
import math
import os
import json
import re
import subprocess
import hashlib

import requests

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

# Delete files matching the pattern "*piece[0-9]*" in the temp directory
if os.path.exists(f"./temp"):
    print("ii INFO: Cleaning up temp directory...")
    for filename in os.listdir(f"./temp"):
        if re.search(r"piece+\d", filename):
            os.remove(os.path.join(sourceloc, filename))
    print("ii INFO: Temp directory cleared.")
else:
    print("ii INFO: Creating temp directory...")
    os.mkdir(f"./temp")
    print("ii INFO: Temp directory created.")

# PROGRAM INTERNAL VARS
useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
useragent += "(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
baseurltb = "https://www.terabox.com"


# PROGRAM FUNCTIONS
def convert_size(size_bytes: int):
    """Converts bytes to human-readable size"""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    size = round(size_bytes / p, 2)
    return f"{size} {size_name[i]}"


# Show files to upload
print()
print("Files to upload:")
for filename in os.listdir(sourceloc):
    fsizebytes = os.path.getsize(os.path.join(sourceloc, filename))
    fsize = convert_size(fsizebytes)
    print(f" - {filename} ({fsize})")

# Get member info and check if the user is a VIP
vimemberreq = requests.get(
    f"{baseurltb}/rest/2.0/membership/proxy/user?method=query",
    headers={"User-Agent": useragent},
    cookies=cookies,
)
member_info = json.loads(vimemberreq.text)["data"]["member_info"]
vip = member_info["is_vip"]
print(f"\nii INFO: You are a {'vip' if vip == 1 else 'non-vip'} user.")

# Loop through files in source directory and add to array
files = []
for filename in os.listdir(sourceloc):
    if os.path.isfile(os.path.join(sourceloc, filename)):
        fsizebytes = os.path.getsize(os.path.join(sourceloc, filename))
        files.append({"name": filename, "sizebytes": fsizebytes})

for file in files:
    print(f"\n/\\ UPLOAD: Uploading {file['name']}...")

    # QUOTA CALCULATIONS
    response = requests.get(
        f"{baseurltb}/api/quota?checkfree=1",
        headers={"User-Agent": useragent},
        cookies=cookies,
    )
    quota = json.loads(response.text)
    totquot = quota["total"]  # total quota available
    usequot = quota["used"]  # used quota
    aviquot = quota['total'] - quota['used']  # available quota
    print(f"ii INFO: Available quota: {convert_size(aviquot)}")
    if aviquot < file["sizebytes"]:
        print(f"!! ERROR: not enough quota available for file {file["name"]}.")
        continue
    print(f"ii INFO: Available quota after the upload: {convert_size(aviquot - file["sizebytes"])}")

    # UPLOAD PROCEDURE
    if not os.path.exists(f"{sourceloc}/{file["name"]}"):
        print(f"!! ERROR: File {file["name"]} does not exist on source directory anymore. Skipping...")
        continue

    if (vip == 1 and file["sizebytes"] <= 21474836479) or (vip == 0 and file["sizebytes"] <= 4294967296):
        pieces = []
        if file["sizebytes"] >= 2147483648:
            print("ii INFO: File size is greater than 2GB. Uploading in chunks...")
            subprocess.run(
                [
                    "split",
                    "-b",
                    "120M",
                    "-a",
                    "3",
                    f"{sourceloc}/{file["name"]}",
                    f"./temp/{file["name"]}.part",
                ]
            )
            print("ii INFO: Calculating MD5 hashes...")
            md5dict = []
            for i, infile in enumerate(sorted(glob.glob('./temp/' + file["name"] + '.part*'))):
                # rename the files to have a 3-digit suffix
                newname = f"./temp/{file["name"]}.part{i:03}"
                os.rename(infile, newname)
                md5dict.append(hashlib.md5(open(newname, 'rb').read()).hexdigest())
                # add the piece file to the pieces array
                pieces.append(newname)
            md5json = json.dumps(md5dict)
            print("ii INFO: MD5 hashes calculated.")
        else:
            md5dict = []
            print("ii INFO: Calculating MD5 hashes...")
            md5dict.append(hashlib.md5(open(f"{sourceloc}/{file["name"]}", 'rb').read()).hexdigest())
            print("ii INFO: MD5 hashes calculated.")
            md5json = json.dumps(md5dict)
            pieces.append(f"{sourceloc}/{file["name"]}")

        cloudpath = remoteloc + "/" + file["name"]
        data = {
            "app_id": "250528",
            "web": "1",
            "channel": "dubox",
            "clienttype": "0",
            "jsToken": f"{jstoken}",
            "path": f"{cloudpath}",
            "autoinit": "1",
            "target_path": f"{remoteloc}",
            "block_list": f"{md5json}",
        }

        response = requests.post(f"{baseurltb}/api/precreate",
                                 headers={"User-Agent": useragent, "Origin": baseurltb,
                                          "Referer": baseurltb + "/main?category=all",
                                          "Content-Type": "application/x-www-form-urlencoded"},
                                 cookies=cookies,
                                 data=data)

        if "uploadid" in response.text:
            uploadid = json.loads(response.text)["uploadid"]
            print(f"ii INFO: Precreate for upload ID \"{uploadid}\" successful.")
            numpieces = len(pieces)

            if numpieces > 1:
                print(f"ii INFO: Number of pieces to be uploaded: {numpieces}")

                for i, pi in enumerate(pieces):
                    print(f"ii INFO: Uploading piece {pieces.index(pi) + 1} of {numpieces}...")
                    data = {
                        "type": "tmpfile",
                        "app_id": "250528",
                        "path": f"{cloudpath}",
                        "uploadid": uploadid,
                        "partseq": i,
                    }
                    response = requests.post(
                        f"{baseurltb.replace('www', 'c-jp')}/rest/2.0/pcs/superfile2?method=upload",
                        headers={"User-Agent": useragent, "Origin": baseurltb, "Content-Type": "multipart/form-data"},
                        cookies=cookies,
                        files={"file": open(pi, "rb")},
                        params=data,
                    )
                    if response.status_code == 200:
                        print(f"ii INFO: Piece {pieces.index(pi) + 1} of {numpieces} uploaded successfully.")
                    else:
                        print(f"!! ERROR: Piece {pieces.index(pi) + 1} of {numpieces} upload failed.")
                        break
            else:
                print(f"ii INFO: Uploading file {file["name"]}...")
                data = {
                    "type": "tmpfile",
                    "app_id": "250528",
                    "path": f"{cloudpath}",
                    "uploadid": uploadid,
                    "partseq": "0",
                }
                try:
                    response = requests.post(
                        f"{baseurltb.replace('www', 'c-jp')}/rest/2.0/pcs/superfile2?method=upload",
                        headers={"User-Agent": useragent, "Origin": baseurltb},
                        cookies=cookies,
                        files={"file": open(f"{sourceloc}/{file["name"]}", "rb")},
                        params=data,
                    )
                    print(response.text)
                    md5hash = response.json()["md5"]
                    if md5hash == md5dict[0]:
                        params = {
                            "isdir": "0",
                            "rtype": "1",
                            "bdstoken": f"{bdstoken}",
                            "app_id": "250528",
                            "jsToken": f"{jstoken}"
                        }
                        data = {
                            "path": f"{cloudpath}",
                            "uploadid": f"{uploadid}",
                            "target_path": f"{remoteloc}/",
                            "size": f"{file["sizebytes"]}",
                            "block_list": f"{md5json}",
                        }
                        response = requests.post(
                            f"{baseurltb}/api/create",
                            headers={"User-Agent": useragent, "Origin": baseurltb, "Content-Type": "application/x-www"
                                                                                                   "-form-urlencoded"},
                            cookies=cookies,
                            params=params,
                            data=data,
                        )
                        create = json.loads(response.text)
                        if create["errno"] == 0:
                            print(f"ii INFO: File {file["name"]} uploaded successfully.")
                            if movefiles:
                                print(f"ii INFO: Moving file {file["name"]} to {movetoloc}...")
                                os.rename(f"{sourceloc}/{file["name"]}", f"{movetoloc}/{file["name"]}")
                                print(f"ii INFO: File {file["name"]} moved successfully.")
                    else:
                        print(f"ii ERROR: MD5 hash mismatch for file {file["name"]} after upload. Skipping file...")
                        print(f"ii ERROR: Expected: {md5dict[0]}")
                        print(f"ii ERROR: Received: {md5hash}")
                        continue

                except Exception as e:
                    print(f"!! ERROR: File upload failed. Server returned status code {response.status_code}.")
                    print(f"!! ERROR: More information: {e}")
                    continue
        else:
            print("!! ERROR: Precreate for file failed. Skipping file...")
            continue
