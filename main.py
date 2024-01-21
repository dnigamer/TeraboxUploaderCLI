import glob
import math
import os
import json
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

print("ii INFO: Loading secrets...")
with open("secrets.json", "r") as f:
    secrets = json.load(f)
    jstoken = secrets["jstoken"]
    bdstoken = secrets["bdstoken"]
    cookies = secrets["cookies"]
    f.close()

if not (any(char.isdigit() for char in jstoken) and any(char.isdigit() for char in bdstoken)):
    print("!! ERROR: Invalid token.")
    exit()
print("ii SUCCESS: Loaded secrets.")

# PROGRAM CONFIGURATION
if not os.path.exists("settings.json"):
    print("!! Error: secrets.json file not found.")
    exit()

print("ii INFO: Loading settings...")
with open("settings.json", "r") as f:
    settings = json.load(f)
    sourceloc = settings["directories"]["sourcedir"]
    remoteloc = settings["directories"]["remotedir"]
    movetoloc = settings["directories"]["uploadeddir"]
    movefiles = True if settings["settings"]["movefiles"] == "true" else False
    delsrcfil = True if settings["settings"]["deletesource"] == "true" else False
    f.close()

if delsrcfil and movefiles:
    print("!! ERROR: You cannot have move and delete files settings configured as true at the same time.")
    print("!! ERROR: Please check your settings.json file for these configurations.")
    exit()

if not sourceloc or not remoteloc or not movetoloc:
    print("!! ERROR: Invalid directory paths.")
    exit()

if not os.path.exists(sourceloc) and not os.path.isdir(sourceloc):
    print("!! ERROR: Source directory does not exist. Please check the path.")
    exit()

if not os.path.exists(movetoloc) and not os.path.isdir(movetoloc) and movefiles:
    print("!! ERROR: Move to directory does not exist. Please check the path.")
    exit()

print("ii SUCCESS: Loaded settings.")

# PROGRAM INTERNAL VARS
useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
useragent += "(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
baseurltb = "https://www.terabox.com"
temp_directory = "./temp"


# PROGRAM FUNCTIONS
def convert_size(size_bytes: int):
    """Converts bytes to human-readable size"""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    it = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, it)
    size = round(size_bytes / p, 2)
    return f"{size} {size_name[it]}"


def precreate_file(filenam: str, md5json: str):
    """Precreates a file for upload"""
    try:
        preresponse = requests.post(f"{baseurltb}/api/precreate",
                                    headers={"User-Agent": useragent, "Origin": baseurltb,
                                             "Referer": baseurltb + "/main?category=all",
                                             "Content-Type": "application/x-www-form-urlencoded"},
                                    cookies=cookies,
                                    data={
                                        "app_id": "250528",
                                        "web": "1",
                                        "channel": "dubox",
                                        "clienttype": "0",
                                        "jsToken": f"{jstoken}",
                                        "path": f"{remoteloc + "/" + filenam}",
                                        "autoinit": "1",
                                        "target_path": f"{remoteloc}",
                                        "block_list": f"{md5json}",
                                    })
        if "uploadid" in preresponse.text:
            return json.loads(preresponse.text)["uploadid"]
        else:
            print(f"!! ERROR: File precreate failed. Server returned status code {preresponse.status_code}.")
            if (json.loads(preresponse.text)["errmsg"] == 'need verify' or json.loads(preresponse.text)["errno"] ==
                    '4000023'):
                print("!! ERROR: The login session has expired. Please login again and refresh the credentials.")
            print(f"!! ERROR: More information: {json.loads(preresponse.text)}")
            return "fail"
    except Exception as e:
        print(f"!! ERROR: File precreate request failed.")
        print(f"!! ERROR: More information about this error: {e}")
        return "fail"


def upload_file(filename: str, uploadid: str, md5hash: str):
    """Uploads a file"""
    try:
        upresponse = requests.post(
            f"{baseurltb.replace('www', 'c-jp')}/rest/2.0/pcs/superfile2?method=upload",
            headers={"User-Agent": useragent, "Origin": baseurltb},
            cookies=cookies,
            files={"file": open(f"{sourceloc}/{filename}", "rb")},
            params={
                "type": "tmpfile",
                "app_id": "250528",
                "path": f"{remoteloc + '/' + filename}",
                "uploadid": uploadid,
                "partseq": "0",
            },
        )
        print(upresponse.text)
        if upresponse.status_code == 200:
            md5serv = upresponse.json()["md5"]
            if md5serv == md5hash:
                print(f"ii UPLOAD: MD5 hash match for file {file["name"]} after upload.")
                return md5serv
            else:
                print(f"ii ERROR: MD5 hash mismatch for file {file["name"]} after upload. Skipping file...")
                return "mismatch"
    except Exception as e:
        print(f"!! ERROR: File upload request failed.")
        print(f"!! ERROR: More information about this error: {e}")
        return "failed"


def create_file(cloudpath: str, uploadid: str, sizebytes: int, md5json: str) -> requests.Response:
    crresponse = requests.post(
        f"{baseurltb}/api/create",
        headers={"User-Agent": useragent, "Origin": baseurltb, "Content-Type": "application/x-www"
                                                                               "-form-urlencoded"},
        cookies=cookies,
        params={
            "isdir": "0",
            "rtype": "1",
            "bdstoken": f"{bdstoken}",
            "app_id": "250528",
            "jsToken": f"{jstoken}"
        },
        data={
            "path": f"{cloudpath}",
            "uploadid": f"{uploadid}",
            "target_path": f"{remoteloc}/",
            "size": f"{sizebytes}",
            "block_list": f"{md5json}",
        },
    )
    return crresponse


def clean_temp():
    """Cleans the temp folder"""
    if os.path.exists(temp_directory):
        print("ii INFO: Cleaning up temp directory...")
        for filename in os.listdir(temp_directory):
            file_path = os.path.join(temp_directory, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"!! ERROR: File {filename} could not be deleted.")
                print(f"!! ERROR: More information about this error: {e}")
                return False
        print("ii SUCCESS: Temp directory cleared.")
        return True
    else:
        print("ii INFO: Creating temp directory...")
        os.mkdir(temp_directory)
        print("ii SUCCESS: Temp directory created.")
        return True


# PROGRAM START
clean_temp()  # Clean temp directory

# Get member info and check if the user is a VIP
print("\nii INFO: Checking if you are a VIP user...")
vimemberreq = requests.get(
    f"{baseurltb}/rest/2.0/membership/proxy/user?method=query",
    headers={"User-Agent": useragent},
    cookies=cookies,
)
member_info = json.loads(vimemberreq.text)["data"]["member_info"]
vip = member_info["is_vip"]
print(f"ii INFO: You are a {'vip' if vip == 1 else 'non-vip'} user.")

# Loop through files in source directory and add to array
files = []
print("\nii INFO: Files to upload:")
for filename in os.listdir(sourceloc):
    if os.path.isfile(os.path.join(sourceloc, filename)):
        if filename in [".DS_Store", "main.py", "settings.json", "secrets.json"]:
            print(f"ii INFO: Skipping file {filename} because it's a protected file.")
            continue
        fsizebytes = os.path.getsize(os.path.join(sourceloc, filename))
        print(f" - {filename} ({convert_size(fsizebytes)})")
        files.append({"name": filename, "sizebytes": fsizebytes})

for file in files:
    print(f"\n/\\ UPLOAD: Uploading {file['name']}...")

    # QUOTA CALCULATIONS
    quotareq = requests.get(
        f"{baseurltb}/api/quota?checkfree=1",
        headers={"User-Agent": useragent},
        cookies=cookies,
    )
    quota = json.loads(quotareq.text)
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
        print(f"!! ERROR: File {file["name"]} does not exist on source directory anymore. Skipping file...")
        continue

    if (vip == 1 and file["sizebytes"] >= 21474836479) or (vip == 0 and file["sizebytes"] >= 4294967296):
        print(f"!! ERROR: File {file["name"]} is too big for the type of account you have. Skipping file...")
        print(f"!! ERROR: File size: {convert_size(file["sizebytes"])}")
        print(f"!! ERROR: Maximum file size for your account: {'20GB' if vip == 1 else '4GB'}")
        continue

    pieces = []
    if file["sizebytes"] >= 2147483648:
        print("ii SPLIT: File size is greater than 2GB. Uploading in chunks...")
        subprocess.run(  # WORKS IN MACOS. TO BE TESTED IN LINUX. NEEDS REIMPLEMENTATION FOR WINDOWS.
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
        print("ii MD5: Calculating MD5 hashes...")
        md5dict = []
        for i, infile in enumerate(sorted(glob.glob('./temp/' + file["name"] + '.part*'))):
            # rename the files to have a 3-digit suffix
            newname = f"./temp/{file["name"]}.part{i:03}"
            os.rename(infile, newname)
            md5dict.append(hashlib.md5(open(newname, 'rb').read()).hexdigest())
            # add the piece file path to the pieces array
            pieces.append(newname)
        md5json = json.dumps(md5dict)
        print("ii MD5: MD5 hashes calculated.")
    else:
        md5dict = []
        print("ii MD5: Calculating MD5 hashes...")
        md5dict.append(hashlib.md5(open(f"{sourceloc}/{file["name"]}", 'rb').read()).hexdigest())
        print("ii MD5: MD5 hashes calculated.")
        md5json = json.dumps(md5dict)
        pieces.append(f"{sourceloc}/{file["name"]}")

    # Preinitialize the full file on the cloud
    print("ii PRECREATE: Precreating file...")
    uploadid = precreate_file(file["name"], md5json)
    if uploadid == "fail":
        continue
    print(f"ii PRECREATE: Precreate for upload ID \"{uploadid}\" successful.")
    cloudpath = remoteloc + "/" + file["name"]

    if len(pieces) > 1:
        print(f"ii UPLOAD: Number of pieces to be uploaded: {len(pieces)}")
        print(f"ii PIECE UPLOAD: Commencing upload of file {file["name"]} in pieces...")

        # Upload the pieces
        for i, pi in enumerate(pieces):
            print(f"ii PIECE UPLOAD: Uploading piece {pieces.index(pi) + 1} of {len(pieces)}...")
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
                print(f"ii PIECE UPLOAD: Piece {pieces.index(pi) + 1} of {len(pieces)} uploaded successfully.")
            else:
                print(f"!! ERROR: Piece {pieces.index(pi) + 1} of {len(pieces)} upload failed.")
                print(f"!! ERROR: Server returned status code {response.status_code}.")
                print(f"!! ERROR: More information: {json.loads(response.text)}")
                print(f"!! ERROR: Skipping file {file["name"]}...")
                break

        print("ii PIECE UPLOAD: All pieces uploaded successfully.")
    else:
        print(f"ii UPLOAD: Uploading file {file["name"]}...")

        uploadhash = upload_file(file["name"], uploadid, md5dict[0])
        if uploadhash == "failed":
            continue
        if uploadhash == "mismatch":
            continue

    print(f"ii UPLOAD: Finalizing file {file["name"]} upload...")
    # Create the file
    create = create_file(cloudpath, uploadid, file["sizebytes"], md5json)
    if json.loads(create.text)["errno"] == 0:
        print(f"ii UPLOAD: File {file["name"]} uploaded successfully.")
    else:
        print(f"!! ERROR: File {file["name"]} upload failed.")
        print(f"!! ERROR: More information: {create}")
        continue

    if movefiles:
        print(f"ii MOVE: Moving file {sourceloc}/{file["name"]} to {movetoloc}/{file["name"]}...")
        try:
            os.rename(f"{sourceloc}/{file["name"]}", f"{movetoloc}/{file["name"]}")
            print(f"ii MOVE: File {file["name"]} moved successfully to destination.")
        except Exception as e:
            print(f"!! ERROR: File {file["name"]} could not be moved.")
            print(f"!! ERROR: More information about this error: {e}")
            continue

    if delsrcfil:
        print(f"ii DELETE: Deleting file {file["name"]} from source directory...")
        try:
            os.remove(f"{sourceloc}/{file["name"]}")
            print(f"ii DELETE: File {file["name"]} deleted successfully.")
        except Exception as e:
            print(f"!! ERROR: File {file["name"]} could not be deleted.")
            print(f"!! ERROR: More information about this error: {e}")
            continue

