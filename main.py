import fnmatch
import math
import os
import sys
import json
import subprocess
import hashlib
import zipfile
from urllib.parse import quote_plus
import requests

from modules.encryption import Encryption, FileEncryptedException
from modules.formatting import Formatting

fmt = Formatting(timestamps=True)

print("-" * 97)
print("Terabox Uploader CLI v1.5.0 2024")
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
    fmt.info("CURL", "Windows host detected. Checking if curl is installed...")
    if not os.path.exists("curl/bin/curl.exe") or not os.path.exists("curl.exe"):
        fmt.info("CURL", f"curl.exe not found. Downloading curl from {CURL_URL}...")
        curlreq = requests.get(CURL_URL, timeout=10)
        with open("curl.zip", "wb") as f:
            f.write(curlreq.content)
            f.close()
        fmt.info("CURL", "Extracting curl...")
        with zipfile.ZipFile("curl.zip", "r") as zip_ref:
            zip_ref.extractall(".")
            zip_ref.close()
        os.rename("curl-8.5.0_5-win64-mingw", "curl")
        fmt.info("CURL", "Curl extracted.")
        os.remove("curl.zip")
    else:
        fmt.success("CURL", "curl is already installed or exists in the current folder.")
else:
    fmt.info("CURL", "Checking for curl...")
    if not subprocess.run(["which", "curl"], stdout=subprocess.PIPE).stdout.decode('utf-8'):
        fmt.info("CURL", "curl not found. Installing curl...")
        if os.name == "posix":
            fmt.info("CURL", "Installing curl using Homebrew...")
            subprocess.run(["brew", "install", "curl"])
        elif os.name == "linux":  # Assuming Debian-based distros
            fmt.info("CURL", "Installing curl using apt...")
            subprocess.run(["sudo", "apt", "install", "-y", "curl"])
        else:
            fmt.error("CURL", "Your OS is not supported for automatic curl installation. Please install curl manually.")
            sys.exit()
    else:
        fmt.info("CURL", "Curl is already installed or exists in the current folder.")

# TERABOX AUTHENTICATION
if not os.path.exists("secrets.json"):
    fmt.error("auth", "secrets.json file not found.")
    fmt.error("auth", "Please create a secrets.json file with the following format:")
    fmt.error("auth", "{")
    fmt.error("auth", '    "jstoken": "your jstoken token",')
    fmt.error("auth", '    "cookies": {')
    fmt.error("auth", '        "csrfToken": "your csrfToken token",')
    fmt.error("auth", '        "browserid": "your browserid",')
    fmt.error("auth", '        "lang": "your lang (NOT REQUIRED)",')
    fmt.error("auth", '        "ndus": "your ndus token",')
    fmt.error("auth", '        "ndut_fmt": "your ndut_fmt token"')
    fmt.error("auth", '    }')
    fmt.error("auth", "}")
    sys.exit()

with open("secrets.json", "r") as f:
    secrets = json.load(f)
    jstoken = secrets["jstoken"]
    cookies = secrets["cookies"]
    cookies_str = ""
    for key, value in cookies.items():
        cookies_str += f"{key}={value};"
    f.close()

if not (any(char.isdigit() for char in jstoken)):
    fmt.error("auth", "Invalid jstoken.")
    sys.exit()
fmt.success("auth", "Loaded authentication tokens.")

# PROGRAM CONFIGURATION
if not os.path.exists("settings.json"):
    fmt.error("settings", "settings.json file not found.")
    fmt.error("settings", "Please create a settings.json file with the following format:")
    fmt.error("settings", "{")
    fmt.error("settings", '    "directories": {')
    fmt.error("settings", '        "sourcedir": "path to the source directory",')
    fmt.error("settings", '        "remotedir": "path to the remote directory",')
    fmt.error("settings", '        "uploadeddir": "path to the uploaded directory"')
    fmt.error("settings", '    },')
    fmt.error("settings", '    "files": {')
    fmt.error("settings", '        "movefiles": "true or false",')
    fmt.error("settings", '        "deletesource": "true or false"')
    fmt.error("settings", '    },')
    fmt.error("settings", '    "encryption": {')
    fmt.error("settings", '        "enabled": "true or false",')
    fmt.error("settings", '        "encryptionkey": "path to the encryption key"')
    fmt.error("settings", '    },')
    fmt.error("settings", '    "ignoredfiles": ["file1", "file2", "file3", "file4"]')
    fmt.error("settings", "}")
    sys.exit()

with open("settings.json", "r") as f:
    settings = json.load(f)
    sourceloc = settings["directories"]["sourcedir"]
    remoteloc = settings["directories"]["remotedir"]
    movetoloc = settings["directories"]["uploadeddir"]
    movefiles = True if settings["files"]["movefiles"].lower() == "true" else False
    delsrcfil = True if settings["files"]["deletesource"].lower() == "true" else False
    encryptfl = True if settings["encryption"]["enabled"].lower() == "true" else False
    encrypkey = settings["encryption"]["encryptionkey"]
    ignorefil = settings["ignoredfiles"]
    showquota = True if settings["appearance"]["showquota"].lower() == "true" else False
    f.close()

if delsrcfil and movefiles:
    fmt.error("settings", "You cannot have move and delete files settings configured as true at the same time.")
    fmt.error("settings", "Please check your settings.json file for these configurations.")
    sys.exit()

if not sourceloc or not remoteloc or not movetoloc:
    fmt.error("settings", "Invalid directory paths.")
    sys.exit()

if not os.path.exists(sourceloc) and not os.path.isdir(sourceloc):
    fmt.error("settings", "Source directory does not exist. Please check the path.")
    sys.exit()

if not os.path.exists(movetoloc) and not os.path.isdir(movetoloc) and movefiles:
    fmt.error("settings", "Move to directory does not exist. Please check the path.")
    sys.exit()

if not encryptfl:
    fmt.warning("encryption", "File encryption is disabled. However, it is recommended to enable it for security "
                              "reasons regarding TeraBox's ToS and Privacy Policy.")
    fmt.warning("encryption", "For full security of your files, please enable file encryption in the settings.json "
                              "file.")

encrypt = Encryption()

if encryptfl and not os.path.exists(encrypkey):
    fmt.info("encryption", "Generating encryption key...")
    encrypt.generate_key(encrypkey)
    fmt.success("encryption", "Encryption key generated successfully.")

fmt.success("settings", "Loaded settings.")

# PROGRAM INTERNAL VARS
useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:121.0) Gecko/20100101 Firefox/121.0"
baseurltb = "https://www.terabox1024.com"
temp_directory = "./temp"
ERRORS = False


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
                                    data={"app_id": "250528", "web": "1", "channel": "dubox", "clienttype": "0",
                                          "jsToken": f"{jstoken}", "path": f"{remoteloc}/{filename}", "autoinit": "1",
                                          "target_path": f"{remoteloc}", "block_list": f"{md5json}", })
        if "uploadid" in preresponse.text:
            return json.loads(preresponse.text)["uploadid"]
        else:
            fmt.error("precreate", "File precreate failed.")
            if json.loads(preresponse.text)["errmsg"] == 'need verify':
                fmt.error("precreate", "The login session has expired. Please login again and refresh the credentials.")
                return "fail"
            fmt.error("precreate", f"ERROR: More information: {json.loads(preresponse.text)}")
            return "fail"
    except Exception as e:
        fmt.error("precreate", "ERROR: File precreate request failed.")
        fmt.error("precreate", f"ERROR: More information about this error: {e}")
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
        base_command = ["curl", "-X", "POST",
                        "-H", f"User-Agent:{useragent}",
                        "-H", f"Origin:{baseurltb}",
                        "-H", f"Referer:{baseurltb}/main?category=all",
                        "-H", "Content-Type:multipart/form-data",
                        "-b", f"{cookies_str}",
                        "-F", f"file=@{filename}",
                        f"{baseurltb.replace('www', 'c-jp')}:443/rest/2.0/pcs/superfile2?"
                        f"method=upload&type=tmpfile&app_id=250528&path={quote_plus(remoteloc + '/' + filename)}&"
                        f"uploadid={uploadid}&partseq={partseq}"]
        if os.name == "nt":
            base_command[0] = "curl/bin/curl.exe"

        out = subprocess.run(base_command, stdout=subprocess.PIPE)
        uresp = json.loads(out.stdout.decode('utf-8'))

        if 'error_code' not in uresp:
            fmt.success("upload", f"File {filename} uploaded successfully.")
            if uresp["md5"] == md5hash:
                fmt.info("md5", f"MD5 hash match for file {filename} after upload.")
                return uresp["md5"]
            else:
                fmt.error("md5", f"MD5 hash mismatch for file {filename} after upload. Skipping file...")
                return "mismatch"
        else:
            fmt.error("upload", "File upload failed.")
            fmt.error("upload", f"ERROR: More information: {uresp}")
            return "failed"
    except Exception as e:
        fmt.error("upload", "File upload request failed.")
        fmt.error("upload", f"More information about this error: {e}")
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
        params={"isdir": "0", "rtype": "1", "app_id": "250528", "jsToken": f"{jstoken}"},
        data={"path": f"{cloudpath}", "uploadid": f"{uploadid}", "target_path": f"{remoteloc}/", "size": f"{sizebytes}",
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
        fmt.info("temp", "Cleaning up temp directory...")
        for tmpfilename in os.listdir(temp_directory):
            file_path = os.path.join(temp_directory, tmpfilename)
            try:
                os.remove(file_path)
            except Exception as e:
                fmt.error("temp", f"File {tmpfilename} could not be deleted.")
                fmt.error("temp", f"More information about this error: {e}")
                return False
        fmt.success("temp", "Temp directory cleared.")
        return True
    else:
        fmt.info("temp", "Creating temp directory...")
        os.mkdir(temp_directory)
        fmt.success("temp", "Temp directory created.")
        return True


# PROGRAM START
clean_temp()  # Clean temp directory

# Get member info and check if the user is a VIP
fmt.info("vip", "Checking if you are a VIP user...")
vip = json.loads(requests.get(f"{baseurltb}/rest/2.0/membership/proxy/user?method=query",
                              headers={"User-Agent": useragent}, cookies=cookies).text)["data"]["member_info"]["is_vip"]
fmt.success("vip", f"You are a {'vip' if vip == 1 else 'non-vip'} user.")


def get_files_in_directory(dir, base_directory):
    dir_files = {}
    for filename in os.listdir(dir):
        full_path = os.path.join(dir, filename)
        if os.path.isfile(full_path):
            if filename in [".DS_Store", os.path.basename(__file__), "settings.json", "secrets.json"]:
                fmt.warning("upload", f"Skipping file {filename} because it's a protected file.")
                continue
            for exclusion in ignorefil:
                if fnmatch.fnmatch(filename, exclusion):
                    fmt.warning("upload", f"Skipping file {filename} because it's in the ignore list.")
                    continue
            sizebytes = os.path.getsize(full_path)
            relpath = os.path.relpath(full_path, base_directory)
            dir_files.setdefault(dir, []).append({"name": filename, "relative_path": relpath, "sizebytes":
                sizebytes, "encrypted": False, "encrypterror": False})
        elif os.path.isdir(full_path):
            dir_files.update(get_files_in_directory(full_path, base_directory))
    return dir_files


# Loop through files in source directory and add to array
files = []
fmt.info("upload", f"Checking files in {sourceloc}...")
files = get_files_in_directory(sourceloc, sourceloc)
if len(files) == 0:
    fmt.success("upload", "No files to upload.")
    fmt.debug("program", "Program closing. Have a nice day!")
    sys.exit()

# ENCRYPTION (IF ENABLED)
if encryptfl:
    if len(files) == 0:
        fmt.success("encrypt", "No files to encrypt.")
        pass

    try:
        key_type = encrypt.get_key_type(encrypkey)
        fmt.debug("encrypt", f"Formatting files using key type: {key_type}")
    except Exception as e:
        fmt.error("encrypt", f"Encryption key {encrypkey} is invalid.")
        fmt.error("encrypt", f"More information about this error: {e}")
        ERRORS = True
        sys.exit()

    fmt.info("encrypt", f"Encrypting files in {sourceloc}...")
    for directory, files_in_directory in files.items():
        for file in files_in_directory:
            fmt.info("encrypt", f"Encrypting file {file['name']}...")
            try:
                encrypt.encrypt_file(encrypkey, os.path.join(str(directory),
                                                             str(file['name'].replace(str(directory), ''))))
                file['name'] = f"{file['name']}.enc"
                file['sizebytes'] = os.path.getsize(os.path.join(temp_directory, file['name']))
                file['encrypted'] = True
                fmt.success("encrypt", f"File {file['name']} encrypted successfully.")
            except FileEncryptedException:
                file['name'] = f"{file['name']}.enc"
                file['sizebytes'] = os.path.getsize(os.path.join(temp_directory, file['name']))
                file['encrypted'] = True
                fmt.warning("encrypt", f"File {file['name']} is already encrypted.")
                continue
            except Exception as e:
                fmt.error("encrypt", f"File {file['name']} encryption failed.")
                fmt.error("encrypt", f"More information about this error: {e}")
                file['encrypterror'] = True
                ERRORS = True
                continue


for directory, files_in_directory in files.items():
    if not files_in_directory:
        continue

    for file in files_in_directory:
        if file['encrypterror']:
            continue

        if file['encrypted']:
            sourceloc = temp_directory
            fmt.debug("file", f"File {file['name']} is encrypted. Using source directory as {temp_directory}.")
        else:
            sourceloc = settings["directories"]["sourcedir"]
            fmt.debug("file", f"File {file['name']} is not encrypted. Using source directory as {sourceloc}.")

        fmt.info("upload", f"Uploading {file['name']}...")

        if showquota:
            # QUOTA CALCULATIONS
            quotareq = requests.get(
                f"{baseurltb}/api/quota?checkfree=1",
                headers={"User-Agent": useragent},
                cookies=cookies,
            )
            quota = json.loads(quotareq.text)
            aviquot = quota['total'] - quota['used']  # available quota

            fmt.debug("quota", f"Available quota: {convert_size(aviquot)}")
            if aviquot < file['sizebytes']:
                fmt.error("quota", f"Not enough quota available for file {file['name']}.")
                continue
            fmt.debug("quota", f"Available quota after the upload: {convert_size(aviquot - file['sizebytes'])}")

        # UPLOAD PROCEDURE
        if not os.path.exists(f"{sourceloc}/{file['name']}"):
            fmt.error("upload", f"File {file['name']} does not exist on the source directory anymore. Skipping file...")
            ERRORS = True
            continue

        if (vip == 1 and file['sizebytes'] >= 21474836479) or (vip == 0 and file['sizebytes'] >= 4294967296):
            fmt.error("upload", f"File {file['name']} is too big for the type of account you have. Skipping file...")
            fmt.error("upload", f"File size: {convert_size(file['sizebytes'])}")
            fmt.error("upload", f"Maximum file size for your account: {'20GB' if vip == 1 else '4GB'}")
            ERRORS = True
            continue

        pieces = []
        if file['sizebytes'] >= 2147483648:
            fmt.info("split", "File size is greater than 2GB. Splitting original file in chunks...")

            md5dict = []
            chunk_size = 120 * 1024 * 1024  # 120MB
            num_chunks = int(os.path.getsize(os.path.join(sourceloc, file['name'])) / chunk_size)
            fmt.debug("split", f"File will be split in {num_chunks} chunks.")

            for i in range(num_chunks):
                chunk_filename = os.path.join(temp_directory, f"{file['name']}.part{i:03d}")
                with open(os.path.join(sourceloc, file['name']), 'rb') as f, open(chunk_filename, 'wb') as chunk_file:
                    f.seek(i * chunk_size)
                    chunk = f.read(chunk_size)
                    chunk_file.write(chunk)
                    md5dict.append(hashlib.md5(chunk).hexdigest())
                pieces.append(chunk_filename)

            fmt.success("split", f"File split successfully in {len(pieces)} pieces.")
            md5json = json.dumps(md5dict)
        else:
            md5dict = [hashlib.md5(open(f"{sourceloc}/{file['name']}", 'rb').read()).hexdigest()]
            fmt.info("md5", f"MD5 hash calculated for file {file['name']}.")
            md5json = json.dumps(md5dict)
            pieces.append(f"{sourceloc}/{file['name']}")

        # Preinitialize the full file on the cloud
        fmt.info("precreate", "Precreating file...")
        relative_path = os.path.join(remoteloc, file['relative_path'].replace(directory, ''))
        if file['encrypted']:
            relative_path += '.enc'
        uploadid = precreate_file(os.path.join(str(remoteloc), str(file['relative_path'].replace(str(directory), ''))),
                                  md5json)
        if uploadid == "fail":
            ERRORS = True
            continue
        cloudpath = relative_path

        if len(pieces) > 1:
            fmt.info("split upload", f"Commencing upload of file {file['name']} in pieces...")

            # Upload the pieces
            for i, pi in enumerate(pieces):
                fmt.debug("split upload", f"Uploading piece {pieces.index(pi) + 1} of {len(pieces)}...")
                upresponse = upload_file(pi, uploadid, md5dict[i], i)
                if upresponse in ("failed", "mismatch"):
                    ERRORS = True
                    continue
                fmt.info("split upload", f"Piece {pieces.index(pi) + 1} of {len(pieces)} uploaded successfully.")
        else:
            fmt.info("upload", f"Uploading file {file['name']}...")
            uploadhash = upload_file(pieces[0], uploadid, md5dict[0])
            if uploadhash in ("failed", "mismatch"):
                ERRORS = True
                continue

        # Create the file on the cloud
        fmt.info("upload", f"Finalizing file {file['name']} upload...")
        create = create_file(cloudpath, uploadid, file['sizebytes'], md5json)
        if json.loads(create.text)["errno"] == 0:
            fmt.success("upload", f"File {file['name']} uploaded and saved on cloud successfully.")
            fmt.success("upload", f"The file is now available at {cloudpath} in the cloud.")
        else:
            fmt.error("upload", f"File {file['name']} upload failed.")
            fmt.error("upload", f"More information: {create}")
            ERRORS = True
            continue

        if movefiles:
            fmt.info("move", f"Moving file {sourceloc}/{file['name']} to {movetoloc}/{file['name']}...")
            try:
                os.rename(f"{sourceloc}/{file['name']}", f"{movetoloc}/{file['name']}")
                fmt.success("move", f"File {file['name']} moved successfully to destination.")
            except Exception as e:
                fmt.error("move", f"File {file['name']} could not be moved.")
                fmt.error("move", f"More information about this error: {e}")
                ERRORS = True
                continue

        if delsrcfil:
            fmt.info("delete", f"Deleting file {file['name']} from source directory...")
            try:
                os.remove(f"{sourceloc}/{file['name']}")
                fmt.success("delete", f"File {file['name']} deleted successfully.")
            except Exception as e:
                fmt.error("delete", f"File {file['name']} could not be deleted.")
                fmt.error("delete", f"More information about this error: {e}")
                ERRORS = True
                continue

        fmt.success("upload", f"File {file['name']} concluded every upload procedure.")

if not ERRORS:
    fmt.success("upload", "All files were uploaded.")
    clean_temp()
    fmt.debug("program", "Program closing. Have a nice day!")
else:
    fmt.warning("upload", "Some files were not uploaded or had problems while uploading. Please check the logs!")
    fmt.debug("program", "Program closing. Have a nice day!")
