import os.path
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class GenerateKeyException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class EncryptFileException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FileEncryptedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DecryptFileException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FileNotEncryptedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Encryption:
    """
    Class to handle encryption and decryption of files
    """

    def __init__(self):
        pass

    @staticmethod
    def generate_key(keyfile='keyfile.key') -> bool:
        """
        Generates a key and saves it to a file
        :param keyfile: keyfile to save the Fernet key to
        :return:
        """
        try:
            Path(keyfile).write_bytes(Fernet.generate_key())
        except Exception as e:
            raise GenerateKeyException(f"Something went wrong when generating key: {e}")
        return True

    @staticmethod
    def encrypt_file(keypath: str, filepath: str) -> bool:
        """
        Encrypts a file using the keyfile
        :param keypath:  path to the keyfile
        :param filepath:  name of the file to encrypt
        :return:
        """

        # VERIFY IF KEYFILE AND FILE EXISTS
        if not os.path.exists(keypath):
            raise EncryptFileException(f"Keyfile {keypath} does not exist.")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist.")

        try:
            fernet = Fernet(Path(keypath).read_bytes())
        except Exception as e:
            raise EncryptFileException(f"Something went wrong when loading keyfile: {e}")

        # VERIFY IF FILE IS ALREADY ENCRYPTED
        if "enc" in filepath:
            original = Path(filepath).read_bytes()
            Path(os.path.join("./temp", f"{os.path.basename(filepath)}.enc")).write_bytes(original)
            raise FileEncryptedException(f"File {filepath} is already encrypted. Reusing file.")

        if Path(filepath).read_bytes().startswith(b"ENC-TERABOXUPLOADERCLI"):
            original = Path(filepath).read_bytes()
            Path(os.path.join("./temp", f"{os.path.basename(filepath)}.enc")).write_bytes(original)
            raise FileEncryptedException(f"File {filepath} is already encrypted.")

        # OPEN FILE, ENCRYPT AND SAVE
        try:
            original = Path(filepath).read_bytes()
        except Exception as e:
            raise EncryptFileException(f"Something went wrong when reading file: {e}")

        try:
            header = b"ENC-TERABOXUPLOADERCLI"
            encrypted = header + fernet.encrypt(original)
        except Exception as e:
            raise EncryptFileException(f"Something went wrong when encrypting file: {e}")

        try:
            Path(os.path.join("./temp", f"{os.path.basename(filepath)}.enc")).write_bytes(encrypted)
        except Exception as e:
            raise EncryptFileException(f"Something went wrong when writing encrypted file: {e}")

        return True

    @staticmethod
    def decrypt_file(keypath: str, filename: str) -> bool:
        """
        Decrypts a file using the keyfile
        :param keypath:  path to the keyfile
        :param filename:  name of the file to decrypt
        :return:
        """
        # VERIFY IF KEYFILE AND FILE EXISTS
        if not os.path.exists(keypath):
            raise DecryptFileException(f"Keyfile {keypath} does not exist.")

        if not os.path.exists(filename):
            raise FileNotFoundError(f"File {filename} does not exist.")

        # VERIFY IF FILE IS ENCRYPTED
        if "enc" not in filename:
            raise FileNotEncryptedException(f"File {filename} is not encrypted.")

        if not Path(filename).read_bytes().startswith(b"ENC-TERABOXUPLOADERCLI"):
            raise FileEncryptedException(f"File {filename} is not encrypted.")

        # OPEN FILE, DECRYPT AND SAVE
        try:
            fernet = Fernet(Path(keypath).read_bytes())
        except Exception as e:
            raise DecryptFileException(f"Something went wrong when loading keyfile: {e}")

        try:
            decrypted = fernet.decrypt(Path(filename).read_bytes())[len(b"ENC-TERABOXUPLOADERCLI"):]
        except InvalidToken:
            raise FileNotEncryptedException(f"Key provided can't decrypt this file.")
        except Exception as e:
            raise DecryptFileException(f"Something went wrong when decrypting file: {e}")

        try:
            Path(filename[:-3]).write_bytes(decrypted)
        except Exception as e:
            raise DecryptFileException(f"Something went wrong when writing decrypted file: {e}")

        return True
