"""
TeraBox Uploader CLI: main.py
Python CLI tool to make uploads to your Terabox cloud from any Linux or Windows environment
without having to use the website.

This program is provided as-is, without any warranty.
This program is not affiliated with Terabox in any way.
This program is licensed under the MIT License.

Developed by Gonçalo M. (@dnigamer in GitHub).
For more information, please visit https://github.com/dnigamer/TeraboxUploaderCLI
If you find any bugs, please open an issue in the GitHub repository mentioned in the link above.
"""

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

CODE_VERSION = "1.6.0"
fmt = Formatting(timestamps=True)

print("-" * 97)
print(f"Terabox Uploader CLI v{CODE_VERSION} 2024")
print("* Developed by Gonçalo M. (@dnigamer in Github).")
print("* For more information, please visit https://github.com/dnigamer/TeraboxUploaderCLI.")
print("* If you find any bugs, please open an issue in the Github repository mentioned in the link above")
print("-" * 97)
print("! This program is licensed under the MIT License.")
print("! This program is provided as-is, without any warranty.")
print("! This program is not affiliated with Terabox in any way.")
print("-" * 97)

if len(sys.argv) > 1 and sys.argv[1] == "setup":
    if os.path.exists("secrets.json") and os.path.exists("settings.json"):
        fmt.error("setup", "secrets.json and settings.json already exist in the current folder.")
        sys.exit()

    if os.path.exists("secrets.json"):
        fmt.error("setup", "secrets.json already exists in the current folder.")
    else:
        fmt.info("setup", "Creating secrets.json file...")
        fmt.info("setup", "Please enter the required information for the secrets.json file.")

        print("Enter your jstoken:")
        JS_TOKEN = input(": ")
        if not any(char.isdigit() for char in JS_TOKEN):
            fmt.error("setup", "Invalid jstoken.")
            sys.exit()

        print("Enter your csrfToken:")
        CSRF_TOKEN = input(": ")
        if not CSRF_TOKEN:
            fmt.error("setup", "Invalid csrfToken.")
            sys.exit()

        print("Enter your browserid:")
        BROWSER_ID = input(": ")
        if not BROWSER_ID:
            fmt.error("setup", "Invalid browserid.")
            sys.exit()

        print("Enter your lang:")
        LANG = input(": ")
        if not LANG:
            LANG = "en"

        print("Enter your ndus token:")
        NDUS = input(": ")
        if not NDUS:
            fmt.error("setup", "Invalid ndus token.")
            sys.exit()

        print("Enter your ndut_fmt token:")
        NDUT_FMT = input(": ")
        if not NDUT_FMT:
            fmt.error("setup", "Invalid ndut_fmt token.")
            sys.exit()

        try:
            with open("secrets.json", "w", encoding="utf8") as f:
                f.write("{\n")
                f.write(f'    "jstoken": "{JS_TOKEN}",\n')
                f.write('    "cookies": {\n')
                f.write(f'        "csrfToken": "{CSRF_TOKEN}",\n')
                f.write(f'        "browserid": "{BROWSER_ID}",\n')
                f.write(f'        "lang": "{LANG}",\n')
                f.write(f'        "ndus": "{NDUS}",\n')
                f.write(f'        "ndut_fmt": "{NDUT_FMT}"\n')
                f.write('    }\n')
                f.write("}\n")
                f.close()
        except Exception as e:
            fmt.error("setup", "An error occurred while creating the secrets.json file.")
            fmt.error("setup", f"More information about this error: {e}")
            sys.exit()

        fmt.success("setup", "secrets.json file created.")

    if os.path.exists("settings.json"):
        fmt.error("setup", "settings.json already exists in the current folder.")
    else:
        fmt.info("setup", "Creating settings.json file...")
        fmt.info("setup", "Please enter the required information for the settings.json file.")

        print("Enter the path to the source directory:")
        SOURCE_DIR = input(": ")
        if not SOURCE_DIR:
            fmt.error("setup", "Invalid source directory.")
            sys.exit()
        if not os.path.exists(SOURCE_DIR):
            fmt.error("setup", "Source directory does not exist.")
            sys.exit()

        print("Enter the path to the remote directory:")
        REMOTE_DIR = input(": ")
        if not REMOTE_DIR:
            fmt.error("setup", "Invalid remote directory.")
            sys.exit()

        print("Do you want to move files to another directory after uploading? (yes/no)")
        MOVE_FILES = input(": ")
        if not MOVE_FILES:
            fmt.error("setup", "Please input \"yes\" or \"no\" for move files setting")
            sys.exit()
        if MOVE_FILES.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid move files setting.")
            fmt.error("setup", "Defaulting to \"false\"/no moving files.")
            MOVE_FILES = "false"
        if MOVE_FILES.lower() == "yes":
            print("Enter the path to the uploaded directory:")
            UPLOADED_DIR = input(": ")
            if not UPLOADED_DIR:
                fmt.error("setup", "Invalid uploaded directory.")
                sys.exit()
            if not os.path.exists(UPLOADED_DIR):
                fmt.error("setup", "Destination directory of uploaded files does not exist.")
                sys.exit()
            MOVE_FILES = "true"
        else:
            MOVE_FILES = "false"
            UPLOADED_DIR = ""

        print("Do you want to delete the source files after uploading? (yes/no)")
        DELETE_SOURCE = input(": ")
        if not DELETE_SOURCE:
            fmt.error("setup", "Please input \"yes\" or \"no\" for delete source setting.")
            sys.exit()
        if DELETE_SOURCE.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid delete source setting. Defaulting to \"false\"/no deletion.")
            DELETE_SOURCE = "false"
        if DELETE_SOURCE.lower() == "yes":
            DELETE_SOURCE = "true"
        else:
            DELETE_SOURCE = "false"

        print("Do you want to enable file encryption? (yes/no)")
        ENCRYPTION_ENAB = input(": ")
        if not ENCRYPTION_ENAB:
            fmt.error("setup", "Please input \"yes\" or \"no\" for encryption setting.")
            sys.exit()
        if ENCRYPTION_ENAB.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid encryption setting.")
            fmt.error("setup", "Defaulting to \"false\"/no encryption.")
            ENCRYPTION_ENAB = "false"
        if ENCRYPTION_ENAB.lower() == "yes":
            print("Enter the path to the encryption key:")
            ENCRYPTION_KEY = input(": ")
            if not ENCRYPTION_KEY:
                fmt.error("setup", "Please input a valid path to the encryption key.")
                sys.exit()
            if os.path.exists(ENCRYPTION_KEY):
                ENCRYPTION_ENAB = "true"
                fmt.success("setup", "Encryption key found.")
                fmt.success("setup", "Type of encryption key: " + Encryption().get_key_type(ENCRYPTION_KEY))
            else:
                fmt.info("setup", "Generating encryption key...")
                encrypt = Encryption()
                encrypt.generate_key(ENCRYPTION_KEY)
                ENCRYPTION_ENAB = "true"
                fmt.success("setup", "Encryption key generated successfully.")
        else:
            ENCRYPTION_ENAB = "false"
            ENCRYPTION_KEY = ""

        print("Do you want to ignore specific files? (yes/no)")
        IGNORE_FILES = input(": ")
        if not IGNORE_FILES:
            fmt.error("setup", "Invalid ignore files setting.")
            sys.exit()
        if IGNORE_FILES.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid ignore files setting.")
        if IGNORE_FILES.lower() == "yes":
            print("Enter the files to ignore separated by a comma (,):")
            IGNORED_FILES = input(": ")
            if not IGNORED_FILES:
                fmt.error("setup", "Invalid ignored files setting.")
                sys.exit()
            IGNORED_FILES = [x.strip() for x in IGNORED_FILES.split(",")]
        else:
            IGNORED_FILES = []

        print("Do you want to show the quota information after each upload? (yes/no)")
        SHOW_QUOTA = input(": ")
        if not SHOW_QUOTA:
            fmt.error("setup", "Invalid show quota setting.")
            sys.exit()
        if SHOW_QUOTA.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid show quota setting.")
        if SHOW_QUOTA.lower() == "yes":
            SHOW_QUOTA = "true"
        else:
            SHOW_QUOTA = "false"

        try:
            with open("settings.json", "w", encoding="utf8") as f:
                f.write("{\n")
                f.write('  "directories": {\n')
                f.write(f'    "sourcedir": "{SOURCE_DIR}",\n')
                f.write(f'    "remotedir": "{REMOTE_DIR}",\n')
                f.write(f'    "uploadeddir": "{UPLOADED_DIR}"\n')
                f.write('  },\n')
                f.write('  "files": {\n')
                f.write(f'    "movefiles": "{MOVE_FILES}",\n')
                f.write(f'    "deletesource": "{DELETE_SOURCE}"\n')
                f.write('  },\n')
                f.write('  "encryption": {\n')
                f.write(f'    "enabled": "{ENCRYPTION_ENAB}",\n')
                f.write(f'    "encryptionkey": "{ENCRYPTION_KEY}"\n')
                f.write('  },\n')
                f.write('  "ignoredfiles": ["' + '", "'.join(IGNORED_FILES) + '"],\n')
                f.write('  "appearance": {\n')
                f.write(f'    "showquota": "{SHOW_QUOTA}"\n')
                f.write('  }\n')
                f.write("}\n")
                f.close()
            fmt.success("setup", "settings.json file created.")
        except Exception as e:
            fmt.error("setup", "An error occurred while creating the settings.json file.")
            fmt.error("setup", f"More information about this error: {e}")
            sys.exit()

    fmt.info("setup", "Setup completed. Please run the program again without the 'setup' argument.")
    sys.exit()

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
    if not subprocess.run(["which", "curl"], stdout=subprocess.PIPE, check=True).stdout.decode('utf-8'):
        fmt.info("CURL", "curl not found. Installing curl...")
        if os.name == "posix":
            fmt.info("CURL", "Installing curl using Homebrew...")
            subprocess.run(["brew", "install", "curl"], check=True)
        elif os.name == "linux":  # Assuming Debian-based distros
            fmt.info("CURL", "Installing curl using apt...")
            subprocess.run(["sudo", "apt", "install", "-y", "curl"], check=True)
        else:
            fmt.error("CURL", "Your OS is not supported for automatic curl installation. Please install curl manually.")
            sys.exit()
    else:
        fmt.info("CURL", "Curl is already installed or exists in the current folder.")

try:
    if not os.path.exists("settings.json"):
        fmt.error("settings", "settings.json file not found.")
        fmt.error("settings", "Please create a settings.json file by running the program with the 'setup'"
                              " argument or following the README.md.")
        sys.exit()

    with open("secrets.json", "r", encoding="utf8") as f:
        try:
            secrets = json.load(f)
        except json.JSONDecodeError as e:
            fmt.error("auth", "Invalid JSON format in secrets.json.")
            fmt.error("auth", f"More information about this error: {e}")
            sys.exit()
        except Exception as e:
            fmt.error("auth", "An error occurred while reading the secrets.json file.")
            fmt.error("auth", f"More information about this error: {e}")
            sys.exit()

        try:
            JSTOKEN = secrets["jstoken"]
            COOKIES = secrets["cookies"]
            COOKIES_STR = ""
            for key, value in COOKIES.items():
                COOKIES_STR += f"{key}={value};"
            f.close()

            if not any(char.isdigit() for char in JSTOKEN):
                fmt.error("auth", "Invalid jstoken.")
                sys.exit()
            fmt.success("auth", "Loaded authentication tokens.")
        except KeyError as e:
            fmt.error("auth", f"Key {e} not found in secrets.json.")
            f.close()
            sys.exit()
        except Exception as e:
            fmt.error("auth", "An error occurred while reading the secrets.json file.")
            fmt.error("auth", f"More information about this error: {e}")
            f.close()
            sys.exit()
except FileNotFoundError as e:
    fmt.error("auth", "secrets.json file not found.")
    fmt.error("auth", f"More information about this error: {e}")
    sys.exit()
except Exception as e:
    fmt.error("auth", "An error occurred while reading the secrets.json file.")
    fmt.error("auth", f"More information about this error: {e}")
    sys.exit()

try:
    if not os.path.exists("settings.json"):
        fmt.error("settings", "settings.json file not found.")
        fmt.error("settings",
                  "Please create a settings.json file by running the program with the 'setup' argument or following "
                  "the README.md.")
        sys.exit()

    with open("settings.json", "r", encoding="utf8") as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError as e:
            fmt.error("settings", "Invalid JSON format in settings.json.")
            fmt.error("settings", f"More information about this error: {e}")
            sys.exit()
        except Exception as e:
            fmt.error("settings", "An error occurred while reading the settings.json file.")
            fmt.error("settings", f"More information about this error: {e}")
            sys.exit()

        try:
            SOURCE_DIR = settings["directories"].get("sourcedir", "")
            REMOTELOC = settings["directories"].get("remotedir", "")
            MOVETOLOC = settings["directories"].get("uploadeddir", "")
            MOVEFILES = settings["files"].get("movefiles", "false").lower() == "true"
            DELSRCFIL = settings["files"].get("deletesource", "false").lower() == "true"
            ENCRYPTFL = settings["encryption"].get("enabled", "false").lower() == "true"
            ENCRYPKEY = settings["encryption"].get("encryptionkey", "")
            IGNOREFIL = settings.get("ignoredfiles", [])
            SHOWQUOTA = settings["appearance"].get("showquota", "false").lower() == "true"
        except KeyError as e:
            fmt.error("settings", f"Key {e} not found in settings.json.")
            fmt.error("settings", "Please check your settings.json file and the README.md file for these "
                                  "configurations.")
            sys.exit()
        except Exception as e:
            fmt.error("settings", "An error occurred while reading the settings.json file.")
            fmt.error("settings", f"More information about this error: {e}")
            sys.exit()
        f.close()
except FileNotFoundError as e:
    fmt.error("settings", "settings.json file not found.")
    fmt.error("settings", f"More information about this error: {e}")
    sys.exit()
except Exception as e:
    fmt.error("settings", "An error occurred while reading the settings.json file.")
    fmt.error("settings", f"More information about this error: {e}")
    sys.exit()

if DELSRCFIL and MOVEFILES:
    fmt.error("settings",
              "You cannot have move and delete files settings configured as true at the same time.")
    fmt.error("settings", "Please check your settings.json file for these configurations.")
    sys.exit()

if not SOURCE_DIR or not REMOTELOC:
    fmt.error("settings", "Invalid directory paths. Please check the settings.json file for missing paths.")
    sys.exit()

if not os.path.exists(SOURCE_DIR) and not os.path.isdir(SOURCE_DIR):
    fmt.error("settings", "Source directory does not exist. Please check the path.")
    sys.exit()

if not os.path.exists(MOVETOLOC) and not os.path.isdir(MOVETOLOC) and MOVEFILES:
    fmt.error("settings", "Move to directory does not exist. Please check the path.")
    sys.exit()

if not ENCRYPTFL:
    fmt.warning("encryption",
                "File encryption is disabled. However, it is recommended to enable it for security "
                "reasons regarding TeraBox's ToS and Privacy Policy.")
    fmt.warning("encryption",
                "For full security of your files, please enable file encryption in the settings.json "
                "file.")
else:
    encrypt = Encryption()
    if not ENCRYPKEY:
        fmt.error("encryption", "Encryption key path is not set.")
        sys.exit()
    if not os.path.exists(ENCRYPKEY):
        fmt.warning("encryption", "Encryption key file does not exist.")
        fmt.info("encryption", "Generating encryption key...")
        encrypt.generate_key(ENCRYPKEY)
        fmt.success("encryption", "Encryption key generated successfully.")
    else:
        fmt.success("encryption", "Encryption key found.")
        fmt.success("encryption", "Type of encryption key: " + encrypt.get_key_type(ENCRYPKEY))

fmt.success("settings", "Loaded settings.")

# PROGRAM INTERNAL VARS
USERAGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:121.0) Gecko/20100101 Firefox/121.0"
BASEURLTB = "https://www.terabox1024.com"
TEMP_DIR = "./temp"
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


def fetch_remote_directory(remote_dir: str) -> list:
    """
    Returns all the files in the remote directory in a list
    :param remote_dir:
    :return: list of files/folders in the remote directory
    """
    req = requests.get(f"{BASEURLTB}/api/list",
                       headers={"User-Agent": USERAGENT, "Origin": BASEURLTB,
                                "Referer": BASEURLTB + "/main?category=all",
                                "Content-Type": "application/x-www-form-urlencoded"},
                       cookies=COOKIES,
                       data={"app_id": "250528", "web": "1", "channel": "dubox", "clienttype": "0",
                             "jsToken": f"{JSTOKEN}", "dir": f"{remote_dir}", "num": "1000", "page": "1"}, timeout=10)
    response = json.loads(req.text)["list"]
    items = []
    for entry in response:
        listing = {
            "name": entry["server_filename"],
            "path": entry["path"],
            "size": entry["size"],
        }
        if entry["isdir"] == 0:  # If the entry is a file, add the MD5 hash
            items.append(listing)
        if entry["isdir"] == 1:  # If the entry is a directory, recursively fetch its content
            items.extend(fetch_remote_directory(entry["path"]))
    return items


def precreate_file(filename: str, md5json_pc_local: str) -> str:
    """
    Precreates a file for upload
    :param filename: The name of the file to precreate in the cloud path including the filepath.
    :param md5json_pc_local: The MD5 hash of the file or full file (if in pieces).
    :return: The upload ID of the file. If the precreate fails, returns "fail".
    """
    try:
        preresponse = requests.post(f"{BASEURLTB}/api/precreate",
                                    headers={"User-Agent": USERAGENT, "Origin": BASEURLTB,
                                             "Referer": BASEURLTB + "/main?category=all",
                                             "Content-Type": "application/x-www-form-urlencoded"},
                                    cookies=COOKIES,
                                    data={"app_id": "250528", "web": "1", "channel": "dubox", "clienttype": "0",
                                          "jsToken": f"{JSTOKEN}", "path": f"{REMOTELOC}/{filename}", "autoinit": "1",
                                          "target_path": f"{REMOTELOC}", "block_list": f"{md5json_pc_local}"},
                                    timeout=10)
        if "uploadid" in preresponse.text:
            return json.loads(preresponse.text)["uploadid"]
        fmt.error("precreate", "File precreate failed.")
        if json.loads(preresponse.text)["errmsg"] == 'need verify':
            fmt.error("precreate",
                      "The login session has expired. Please login again and refresh the credentials.")
            return "fail"
        fmt.error("precreate", f"ERROR: More information: {json.loads(preresponse.text)}")
        return "fail"
    except Exception as exp_precreate:
        fmt.error("precreate", "ERROR: File precreate request failed.")
        fmt.error("precreate", f"ERROR: More information about this error: {exp_precreate}")
        return "fail"


def upload_file(filename: str, uploadid_local: str, md5hash: str, partseq: int = 0) -> str:
    """
    Uploads a file
    :param filename: The name of the file to upload in the cloud path including the filepath.
    :param uploadid_local: The upload ID of the file.
    :param md5hash: The MD5 hash of the file/piece to upload.
    :param partseq: The part sequence of the file. Default is 0 (for single file upload).
    :return: The MD5 hash of the file after upload. If the MD5 hash does not match, returns "mismatch". If the upload
    fails, returns "failed".
    """
    try:
        base_command = ["curl", "-X", "POST",
                        "-H", f"User-Agent:{USERAGENT}",
                        "-H", f"Origin:{BASEURLTB}",
                        "-H", f"Referer:{BASEURLTB}/main?category=all",
                        "-H", "Content-Type:multipart/form-data",
                        "-b", f"{COOKIES_STR}",
                        "-F", f"file=@{filename}",
                        f"{BASEURLTB.replace('www', 'c-jp')}:443/rest/2.0/pcs/superfile2?"
                        f"method=upload&type=tmpfile&app_id=250528&path={quote_plus(REMOTELOC + '/' + filename)}&"
                        f"uploadid={uploadid_local}&partseq={partseq}"]
        if os.name == "nt":
            base_command[0] = "curl/bin/curl.exe"

        out = subprocess.run(base_command, stdout=subprocess.PIPE, check=True)
        uresp = json.loads(out.stdout.decode('utf-8'))

        if 'error_code' not in uresp:
            fmt.success("upload", f"File {filename} uploaded successfully.")
            if uresp["md5"] == md5hash:
                fmt.info("md5", f"MD5 hash match for file {filename} after upload.")
                return uresp["md5"]
            fmt.error("md5", f"MD5 hash mismatch for file {filename} after upload. Skipping file...")
            return "mismatch"

        fmt.error("upload", "File upload failed.")
        fmt.error("upload", f"ERROR: More information: {uresp}")
        return "failed"
    except Exception as exp_upload:
        fmt.error("upload", "File upload request failed.")
        fmt.error("upload", f"More information about this error: {exp_upload}")
        return "failed"


def create_file(cloudpath_local: str, uploadid_local: str, sizebytes: int, md5json_local: str) -> requests.Response:
    """
    Creates a file on the cloud
    :param cloudpath_local: Cloud path of the file to create.
    :param uploadid_local: The upload ID of the file requested previously.
    :param sizebytes: The size of the file in bytes.
    :param md5json_local: The MD5 hash of the file or full file (if in pieces).
    :return: The response of the create file request.
    """
    crresponse = requests.post(f"{BASEURLTB}/api/create",
                               headers={"User-Agent": USERAGENT, "Origin": BASEURLTB,
                                        "Content-Type": "application/x-www-form-urlencoded"},
                               cookies=COOKIES,
                               params={"isdir": "0", "rtype": "1", "app_id": "250528", "jsToken": f"{JSTOKEN}"},
                               data={"path": f"{cloudpath_local}", "uploadid": f"{uploadid_local}",
                                     "target_path": f"{REMOTELOC}/", "size": f"{sizebytes}",
                                     "block_list": f"{md5json_local}"},
                               timeout=10)
    return crresponse


def clean_temp() -> bool:
    """
    Cleans the temp folder
    :return: True if the temp folder was cleaned successfully, False otherwise.
    """
    if os.path.exists(TEMP_DIR):
        fmt.info("temp", "Cleaning up temp directory...")
        for tmpfilename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, tmpfilename)
            try:
                os.remove(file_path)
            except Exception as exp_temp:
                fmt.error("temp", f"File {tmpfilename} could not be deleted.")
                fmt.error("temp", f"More information about this error: {exp_temp}")
                return False
        fmt.success("temp", "Temp directory cleared.")
        return True

    fmt.info("temp", "Creating temp directory...")
    os.mkdir(TEMP_DIR)
    fmt.success("temp", "Temp directory created.")
    return True


# PROGRAM START
clean_temp()  # Clean temp directory

# Get member info and check if the user is a VIP
fmt.info("vip", "Checking if you are a VIP user...")
vip = json.loads(requests.get(f"{BASEURLTB}/rest/2.0/membership/proxy/user?method=query",
                              headers={"User-Agent": USERAGENT, "Origin": BASEURLTB,
                                       "Referer": BASEURLTB + "/main?category=all",
                                       "Content-Type": "application/x-www-form-urlencoded"},
                              cookies=COOKIES, timeout=19).text)["data"]["member_info"]["is_vip"]
fmt.success("vip", f"You are a {'vip' if vip == 1 else 'non-vip'} user.")


def get_files_in_directory(find_dir, base_directory) -> dict:
    """
    Recursively gets all files in the source directory
    :param find_dir:             The directory to get files from
    :param base_directory:  The base directory to get the relative path
    :return:                dict of files in the directory
    """
    dir_files = {}
    for filename in os.listdir(find_dir):
        full_path = os.path.join(find_dir, filename)
        if os.path.isfile(full_path):
            if filename in [".DS_Store", os.path.basename(__file__), "settings.json", "secrets.json"]:
                fmt.warning("upload", f"Skipping file {filename} because it's a protected file.")
                continue
            for exclusion in IGNOREFIL:
                if fnmatch.fnmatch(filename, exclusion):
                    fmt.warning("upload", f"Skipping file {filename} because it's in the ignore list.")
                    continue
            sizebytes = os.path.getsize(full_path)
            relpath = os.path.relpath(full_path, base_directory)
            dir_files.setdefault(find_dir, []).append({"name": filename, "relative_path": relpath, "sizebytes":
                                                       sizebytes, "encrypted": False, "encrypterror": False})
        elif os.path.isdir(full_path):
            dir_files.update(get_files_in_directory(full_path, base_directory))
    return dir_files


# Loop through files in source directory and add to array
fmt.info("upload", f"Checking files in {SOURCE_DIR}...")
files = get_files_in_directory(SOURCE_DIR, SOURCE_DIR)
if len(files) == 0:
    fmt.success("upload", "No files to upload.")
    fmt.debug("program", "Program closing. Have a nice day!")
    sys.exit()

# ENCRYPTION (IF ENABLED)
if ENCRYPTFL:
    encrypt = Encryption()
    if len(files) == 0:
        fmt.success("encrypt", "No files to encrypt.")

    try:
        KEY_TYPE = encrypt.get_key_type(ENCRYPKEY)
        fmt.debug("encrypt", f"Formatting files using key type: {KEY_TYPE}")
    except Exception as e:
        fmt.error("encrypt", f"Encryption key {ENCRYPKEY} is invalid.")
        fmt.error("encrypt", f"More information about this error: {e}")
        ERRORS = True
        sys.exit()

    fmt.info("encrypt", f"Encrypting files in {SOURCE_DIR}...")
    for directory, files_in_directory in files.items():
        for file in files_in_directory:
            fmt.info("encrypt", f"Encrypting file {file['name']}...")
            try:
                encrypt.encrypt_file(ENCRYPKEY, os.path.join(str(directory),
                                                             str(file['name'].replace(str(directory), ''))))
                file['name'] = f"{file['name']}.enc"
                file['sizebytes'] = os.path.getsize(os.path.join(TEMP_DIR, file['name']))
                file['encrypted'] = True
                fmt.success("encrypt", f"File {file['name']} encrypted successfully.")
            except FileEncryptedException:
                file['name'] = f"{file['name']}.enc"
                file['sizebytes'] = os.path.getsize(os.path.join(TEMP_DIR, file['name']))
                file['encrypted'] = True
                fmt.warning("encrypt", f"File {file['name']} is already encrypted.")
                continue
            except Exception as e:
                fmt.error("encrypt", f"File {file['name']} encryption failed.")
                fmt.error("encrypt", f"More information about this error: {e}")
                file['encrypterror'] = True
                ERRORS = True
                continue

remote_files = fetch_remote_directory(REMOTELOC)
for directory, files_in_directory in files.items():
    if not files_in_directory:
        continue

    for file in files_in_directory:
        if file['encrypterror']:
            continue

        REMOTE_FOUND = False
        for remote_file in remote_files:
            if remote_file["name"] == file["name"]:
                fmt.warning("upload",
                            f"File {file['name']} already exists on the cloud. Skipping file...")
                REMOTE_FOUND = True
        if REMOTE_FOUND:
            continue

        if file['encrypted']:
            SOURCE_DIR = TEMP_DIR
            fmt.debug("file",
                      f"File {file['name']} is encrypted. Using source directory as {TEMP_DIR}.")
        else:
            SOURCE_DIR = settings["directories"]["sourcedir"]
            fmt.debug("file",
                      f"File {file['name']} is not encrypted. Using source directory as {SOURCE_DIR}.")

        fmt.info("upload", f"Uploading {file['name']}...")

        if SHOWQUOTA:
            # QUOTA CALCULATIONS
            quotareq = requests.get("https://{BASEURLTB}/api/quota?checkfree=1",
                                    headers={"User-Agent": USERAGENT},
                                    cookies=COOKIES, timeout=10)
            quota = json.loads(quotareq.text)
            aviquot = quota['total'] - quota['used']  # available quota

            fmt.debug("quota", f"Available quota: {convert_size(aviquot)}")
            if aviquot < file['sizebytes']:
                fmt.error("quota", f"Not enough quota available for file {file['name']}.")
                continue
            fmt.debug("quota",
                      f"Available quota after the upload: {convert_size(aviquot - file['sizebytes'])}")

        # UPLOAD PROCEDURE
        if not os.path.exists(f"{SOURCE_DIR}/{file['name']}"):
            fmt.error("upload",
                      f"File {file['name']} does not exist on the source directory anymore. Skipping file...")
            ERRORS = True
            continue

        if (vip == 1 and file['sizebytes'] >= 21474836479) or (vip == 0 and file['sizebytes'] >= 4294967296):
            fmt.error("upload",
                      f"File {file['name']} is too big for the type of account you have. Skipping file...")
            fmt.error("upload", f"File size: {convert_size(file['sizebytes'])}")
            fmt.error("upload", f"Maximum file size for your account: {'20GB' if vip == 1 else '4GB'}")
            ERRORS = True
            continue

        pieces = []
        if file['sizebytes'] >= 2147483648:
            fmt.info("split", "File size is greater than 2GB. Splitting original file in chunks...")

            md5dict = []
            CHUNK_SIZE = 120 * 1024 * 1024  # 120MB
            num_chunks = int(os.path.getsize(os.path.join(SOURCE_DIR, file['name'])) / CHUNK_SIZE)
            fmt.debug("split", f"File will be split in {num_chunks} chunks.")

            for i in range(num_chunks):
                chunk_filename = os.path.join(TEMP_DIR, f"{file['name']}.part{i:03d}")
                with open(os.path.join(SOURCE_DIR, file['name']), 'rb') as f, open(chunk_filename, 'wb') as chunk_file:
                    f.seek(i * CHUNK_SIZE)
                    chunk = f.read(CHUNK_SIZE)
                    chunk_file.write(chunk)
                    md5dict.append(hashlib.md5(chunk).hexdigest())
                pieces.append(chunk_filename)

            fmt.success("split", f"File split successfully in {len(pieces)} pieces.")
            md5json = json.dumps(md5dict)
        else:
            with open(f"{SOURCE_DIR}/{file['name']}", 'rb') as md5_file:
                md5dict = [hashlib.md5(md5_file.read()).hexdigest()]
            fmt.info("md5", f"MD5 hash calculated for file {file['name']}.")
            md5json = json.dumps(md5dict)
            pieces.append(f"{SOURCE_DIR}/{file['name']}")

        # Preinitialize the full file on the cloud
        fmt.info("precreate", "Precreating file...")
        relative_path = os.path.join(REMOTELOC, file['relative_path'].replace(directory, ''))
        if file['encrypted']:
            relative_path += '.enc'
        uploadid = precreate_file(os.path.join(str(REMOTELOC), str(file['relative_path'].replace(str(directory), ''))),
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
                fmt.info("split upload",
                         f"Piece {pieces.index(pi) + 1} of {len(pieces)} uploaded successfully.")
        else:
            fmt.info("upload", f"Uploading file {file['name']}...")
            uploadhash = upload_file(pieces[0], uploadid, md5dict[0])
            if uploadhash in ("failed", "mismatch"):
                ERRORS = True
                continue

        # Create the file on the cloud
        fmt.info("upload", f"Finalizing file {file['name']} upload...")
        create = create_file(str(cloudpath), uploadid, file['sizebytes'], md5json)
        if json.loads(create.text)["errno"] == 0:
            fmt.success("upload", f"File {file['name']} uploaded and saved on cloud successfully.")
            fmt.success("upload", f"The file is now available at {cloudpath} in the cloud.")
        else:
            fmt.error("upload", f"File {file['name']} upload failed.")
            fmt.error("upload", f"More information: {create}")
            ERRORS = True
            continue

        if MOVEFILES:
            fmt.info("move",
                     f"Moving file {SOURCE_DIR}/{file['name']} to {MOVETOLOC}/{file['name']}...")
            try:
                os.rename(f"{SOURCE_DIR}/{file['name']}", f"{MOVETOLOC}/{file['name']}")
                fmt.success("move", f"File {file['name']} moved successfully to destination.")
            except Exception as e:
                fmt.error("move", f"File {file['name']} could not be moved.")
                fmt.error("move", f"More information about this error: {e}")
                ERRORS = True
                continue

        if DELSRCFIL:
            fmt.info("delete", f"Deleting file {file['name']} from source directory...")
            try:
                os.remove(f"{SOURCE_DIR}/{file['name']}")
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
    fmt.warning("upload",
                "Some files were not uploaded or had problems while uploading. Please check the logs!")
    fmt.debug("program", "Program closing. Have a nice day!")
