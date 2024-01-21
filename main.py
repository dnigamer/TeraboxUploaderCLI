import math
import os
import json
import subprocess
import hashlib
import zipfile

import requests

print("-" * 97)
print("Terabox Uploader CLI v1.0.0 2024")
print("* Developed by Gonçalo M. (@dnigamer in Github).")
print("* For more information, please visit https://github.com/dnigamer/TeraboxUploaderCLI.")
print("* If you find any bugs, please open an issue in the Github repository mentioned in the link above")
print("-" * 97)
print("! This program is licensed under the MIT License.")
print("! This program is provided as-is, without any warranty.")
print("! This program is not affiliated with Terabox in any way.")
print("-" * 97)

# CURL INSTALLATION
CURL_URL = "https://curl.se/windows/dl-8.5.0_5/curl-8.5.0_5-win64-mingw.zip"
if os.name == "nt":
    print("ii DETECT: Windows host detected. Checking if curl is installed...")
    if not os.path.exists("curl/bin/curl.exe") or not os.path.exists("curl.exe"):
        print(f"ii INFO: curl.exe not found. Downloading curl from {CURL_URL}...")
        curlreq = requests.get(CURL_URL)
        with open("curl.zip", "wb") as f:
            f.write(curlreq.content)
            f.close()
        print("ii INFO: Extracting curl...")
        with zipfile.ZipFile("curl.zip", "r") as zip_ref:
            zip_ref.extractall(".")
            zip_ref.close()
        os.rename("curl-8.5.0_5-win64-mingw", "curl")
        print("ii INFO: curl extracted.")
        os.remove("curl.zip")
    else:
        print("ii SUCCESS: curl is already installed or exists in the current folder.")
else:
    print("ii DETECT: Non-Windows host detected. Checking if curl is installed...")
    if not os.path.exists("curl"):
        print("ii INFO: curl not found. Installing curl...")
        if os.name == "posix":
            print("ii INFO: Installing curl using Homebrew...")
            subprocess.run(["brew", "install", "curl"])
        elif os.name == "linux":  # Assuming Debian-based distros
            print("ii INFO: Installing curl using apt...")
            subprocess.run(["sudo", "apt", "install", "-y", "curl"])
        else:
            print("!! ERROR: Your OS is not supported for automatic curl installation. Please install curl manually.")
            exit()
    else:
        print("ii SUCCESS: curl is already installed or exists in the current folder.")

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
    cookies_str = ""
    for key, value in cookies.items():
        cookies_str += f"{key}={value};"
    f.close()

if not (any(char.isdigit() for char in jstoken) and any(char.isdigit() for char in bdstoken)):
    print("!! ERROR: Invalid token.")
    exit()
print("ii SUCCESS: Loaded secrets.")

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
useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:121.0) Gecko/20100101 Firefox/121.0"
baseurltb = "https://www.terabox.com"
temp_directory = "./temp"
errors = False


# PROGRAM FUNCTIONS
def convert_size(size_bytes: int) -> str:
    """
    Converts bytes to human-readable size
    :param size_bytes: The size in bytes to convert.
    :return: The size as a human-readable string.
    """
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    it = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, it)
    size = round(size_bytes / p, 2)
    return f"{size} {size_name[it]}"


def precreate_file(filename: str, md5json: str) -> str:
    """
    Precreates a file for upload
    :param filename: The name of the file to precreate in the cloud path including the filepath.
    :param md5json: The MD5 hash of the file or full file (if in pieces).
    :return: The upload ID of the file. If the precreate fails, returns "fail".
    """
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
                                        "path": f"{remoteloc + "/" + filename}",
                                        "autoinit": "1",
                                        "target_path": f"{remoteloc}",
                                        "block_list": f"{md5json}",
                                    })
        if "uploadid" in preresponse.text:
            return json.loads(preresponse.text)["uploadid"]
        else:
            print(f"!! ERROR: File precreate failed. Server returned status code {preresponse.status_code}.")
            if json.loads(preresponse.text)["errno"] == '4000023':
                print("!! ERROR: The login session has expired. Please login again and refresh the credentials.")
                return "fail"
            print(f"!! ERROR: More information: {json.loads(preresponse.text)}")
            return "fail"
    except Exception as e:
        print(f"!! ERROR: File precreate request failed.")
        print(f"!! ERROR: More information about this error: {e}")
        return "fail"


def upload_file(filename: str, uploadid: str, md5hash: str, partseq: int = 0) -> str:
    """
    Uploads a file
    :param filename: The name of the file to upload in the cloud path including the filepath.
    :param uploadid: The upload ID of the file.
    :param md5hash: The MD5 hash of the file/piece to upload.
    :param partseq: The part sequence of the file. Default is 0 (for single file upload).
    :return: The MD5 hash of the file after upload. If the MD5 hash does not match, returns "mismatch". If the upload
    fails, returns "failed".
    """
    try:
        if os.name == "nt":
            out = subprocess.run(["curl/bin/curl.exe", "-X", "POST",
                                  "-H", f"User-Agent:{useragent}",
                                  "-H", f"Origin:{baseurltb}",
                                  "-H", f"Referer:{baseurltb}/main?category=all",
                                  "-H", "Content-Type:multipart/form-data",
                                  "-b", f"{cookies_str}",
                                  "-F", f"file=@{filename}",
                                  f"{baseurltb.replace('www', 'c-jp')}:443/rest/2.0/pcs/superfile2?"
                                  f"method=upload&type=tmpfile&app_id=250528&path={remoteloc + '/' + filename}&"
                                  f"uploadid={uploadid}&partseq={partseq}"],
                                 stdout=subprocess.PIPE)
        else:
            out = subprocess.run(["curl", "-X", "POST",
                                  "-H", f"User-Agent:{useragent}",
                                  "-H", f"Origin:{baseurltb}",
                                  "-H", f"Referer:{baseurltb}/main?category=all",
                                  "-H", "Content-Type:multipart/form-data",
                                  "-b", f"{cookies_str}",
                                  "-F", f"file=@{filename}",
                                  f"{baseurltb.replace('www', 'c-jp')}:443/rest/2.0/pcs/superfile2?"
                                  f"method=upload&type=tmpfile&app_id=250528&path={remoteloc + '/' + filename}&"
                                  f"uploadid={uploadid}&partseq={partseq}"],
                                 stdout=subprocess.PIPE)
        uresp = json.loads(out.stdout.decode('utf-8'))
        if 'error_code' not in uresp:
            print(f"ii UPLOAD: File {filename} uploaded successfully.")
            if uresp["md5"] == md5hash:
                print(f"ii MD5: MD5 hash match for file {filename} after upload.")
                return uresp["md5"]
            else:
                print(f"ii ERROR: MD5 hash mismatch for file {filename} after upload. Skipping file...")
                return "mismatch"
        else:
            print(f"!! ERROR: File upload failed.")
            print(f"!! ERROR: More information: {uresp}")
            return "failed"
    except Exception as e:
        print(f"!! ERROR: File upload request failed.")
        print(f"!! ERROR: More information about this error: {e}")
        return "failed"


def create_file(cloudpath: str, uploadid: str, sizebytes: int, md5json: str) -> requests.Response:
    """
    Creates a file on the cloud
    :param cloudpath: Cloud path of the file to create.
    :param uploadid: The upload ID of the file requested previously.
    :param sizebytes: The size of the file in bytes.
    :param md5json: The MD5 hash of the file or full file (if in pieces).
    :return: The response of the create file request.
    """
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


def clean_temp() -> bool:
    """
    Cleans the temp folder
    :return: True if the temp folder was cleaned successfully, False otherwise.
    """
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
print("ii VIP: Checking if you are a VIP user...")
vip = json.loads(requests.get(f"{baseurltb}/rest/2.0/membership/proxy/user?method=query",
                              headers={"User-Agent": useragent},
                              cookies=cookies).text)["data"]["member_info"]["is_vip"]
print(f"ii VIP: You are a {'vip' if vip == 1 else 'non-vip'} user.")

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
        print("ii SPLIT: File size is greater than 2GB. Splitting original file in chunks...")
        with open(os.path.join(sourceloc, file["name"]), 'rb') as f:
            content = f.read()
            f.close()

        md5dict = []
        chunk_size = 120 * 1024 * 1024  # 120MB
        num_chunks = int(len(content) / chunk_size)
        print(f"ii SPLIT: File will be split in {num_chunks} chunks.")

        for i in range(num_chunks):
            start = i * chunk_size
            end = min((i + 1) * chunk_size, len(content))
            chunk_filename = f"{os.path.join(temp_directory, f"{file['name']}.part")}{i:03d}"
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(content[start:end])
                chunk_file.close()
            with open(chunk_filename, 'rb') as chunk_file:
                md5dict.append(hashlib.md5(chunk_file.read()).hexdigest())
                chunk_file.close()
            pieces.append(chunk_filename)

        print(f"ii SPLIT: File split successfully in {len(pieces)} pieces.")
        md5json = json.dumps(md5dict)
    else:
        md5dict = [hashlib.md5(open(f"{sourceloc}/{file["name"]}", 'rb').read()).hexdigest()]
        print(f"ii MD5: MD5 hash calculated for file {file["name"]}.")
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
        print(f"ii PIECE UPLOAD: Commencing upload of file {file["name"]} in pieces...")

        # Upload the pieces
        for i, pi in enumerate(pieces):
            print(f"ii PIECE UPLOAD: Uploading piece {pieces.index(pi) + 1} of {len(pieces)}...")
            upresponse = upload_file(pi, uploadid, md5dict[i], i)
            if upresponse in ("failed", "mismatch"):
                continue
            print(f"ii PIECE UPLOAD: Piece {pieces.index(pi) + 1} of {len(pieces)} uploaded successfully.")
        print("ii PIECE UPLOAD: All pieces uploaded successfully.")
    else:
        print(f"ii UPLOAD: Uploading file {file["name"]}...")
        uploadhash = upload_file(pieces[0], uploadid, md5dict[0])
        if uploadhash in ("failed", "mismatch"):
            continue

    # Create the file on the cloud
    print(f"ii UPLOAD: Finalizing file {file["name"]} upload...")
    create = create_file(cloudpath, uploadid, file["sizebytes"], md5json)
    if json.loads(create.text)["errno"] == 0:
        print(f"ii UPLOAD: File {file["name"]} uploaded and saved on cloud successfully.")
        print(f"ii UPLOAD: The file is now available at {remoteloc + '/' + file["name"]} in the cloud.")
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

    print(f"ii SUCCESS: File {file["name"]} concluded every upload procedure.")

if not errors:
    print("\nii INFO: All files were uploaded.")
    clean_temp()
    print("ii INFO: Program closing. Have a nice day!")
else:
    print("ii INFO: Some files were not uploaded. Please check the logs.")
    print("\nii INFO: Program closing. Have a nice day!")
