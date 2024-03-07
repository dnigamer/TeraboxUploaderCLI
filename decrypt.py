from pathlib import Path
import sys

from cryptography.fernet import InvalidToken
from modules.encryption import Encryption, DecryptFileException, FileNotEncryptedException
from modules.formatting import Formatting

fmt = Formatting(timestamps=True)
enc = Encryption()

if len(sys.argv) >= 3:
    keypath = sys.argv[1]
    filepath = sys.argv[2]
else:
    fmt.error("args","Not enough arguments.")
    sys.exit(1)

if not Path(filepath).is_file():
    fmt.error("file","File on provided path don't exist. Please check the path provided.")

if not Path(keypath).is_file():
    fmt.error("file","Key file on provided path don't exist. Please check the path provided.")

try:
    fmt.debug("decrypt", f"Decrypting file {filepath} with key {keypath}")
    enc.decrypt_file(keypath, filepath)
    fmt.success("decrypt", f"File decrypted successfully. File saved as {filepath[:-4]}")
except FileNotFoundError:
    fmt.error("file", "File or keyfile don't exist anymore. Please check the paths provided.")
    fmt.error("file", "Exiting...")
except DecryptFileException as e:
    fmt.error("decrypt", f"Error decrypting file: {e}")
    fmt.error("decrypt", "Exiting...")
except FileNotEncryptedException as e:
    fmt.error("decrypt", "File provided is not encrypted.")
    fmt.error("decrypt", "Exiting...")
except InvalidToken:
    fmt.error("decrypt", "Key provided can't decrypt this file.")
    fmt.error("decrypt", "Exiting...")
