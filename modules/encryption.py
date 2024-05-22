import os
import os.path
from pathlib import Path

import base64
import random
import string
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from modules.formatting import Formatting


class GenerateKeyException(Exception):
    """
    Exception raised when an error occurs during key generation.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class EncryptFileException(Exception):
    """
    Exception raised when an error occurs during file encryption.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FileEncryptedException(Exception):
    """
    Exception raised when a file is already encrypted.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DecryptFileException(Exception):
    """
    Exception raised when an error occurs during file decryption.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FileNotEncryptedException(Exception):
    """
    Exception raised when a file is not encrypted and tried to decrypt.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Encryption:
    """
    Class to handle encryption and decryption of files
    """

    def __init__(self):
        self.chunk_size = 64 * 1024

    @staticmethod
    def generate_key(keyfile='keyfile.key', password=None, key_size=32) -> bool:
        """
        Generates a key and saves it to a file
        :param keyfile: keyfile to save the AES key to
        :param password: password to use for key generation. If None, the user is prompted for a password.
        :param key_size: size of the key to generate in bytes. Must be 16, 24, or 32.
        :return:
        """

        if os.path.exists(keyfile):
            raise FileExistsError(f"Keyfile {keyfile} already exists.")

        if password is None:
            log = Formatting()
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            log.warning("encryption", f"No password provided. Generating random password: {password}")

        password = password.encode()
        salt = os.urandom(16)

        # Use PBKDF2 to derive a secure key from the password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_size,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))  # Derive the key

        try:
            Path(keyfile).write_bytes(key)
        except Exception as e:
            raise GenerateKeyException(f'Something went wrong when generating key: {e}') from e

        return True

    @staticmethod
    def get_key_type(keyfile='keyfile.key') -> str:
        """
        Returns the type of key used in the keyfile
        :param keyfile: path to the keyfile
        :return: "AES" or "Fernet"
        """

        if not os.path.exists(keyfile):
            raise FileNotFoundError(f"Keyfile {keyfile} does not exist.")

        if len(base64.urlsafe_b64decode(Path(keyfile).read_bytes())) == 32:
            return "AES"
        return "Fernet"

    def encrypt_file(self, keypath: str, filepath: str) -> bool:
        """
        Encrypts a file using the keyfile
        :param keypath:  path to the keyfile
        :param filepath:  name of the file to encrypt
        :return:
        """

        # VERIFY IF KEYFILE AND FILE EXISTS
        if not os.path.exists(keypath):
            raise FileNotFoundError(f"Keyfile {keypath} does not exist.")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist.")

        # VERIFY IF FILE IS ALREADY ENCRYPTED
        if "enc" in filepath:
            original = Path(filepath).read_bytes()
            Path(os.path.join("./temp", f"{os.path.basename(filepath)}.enc")).write_bytes(original)
            raise FileEncryptedException(f"File {filepath} is already encrypted. Reusing file.")

        if Path(filepath).read_bytes().startswith(b"ENC-TERABOXUPLOADERCLI"):
            original = Path(filepath).read_bytes()
            Path(os.path.join("./temp", f"{os.path.basename(filepath)}.enc")).write_bytes(original)
            raise FileEncryptedException(f"File {filepath} is already encrypted with Fernet encryption.")

        if Path(filepath).read_bytes().startswith(b"ENC-TERABOXUPLOADERCLI-AES"):
            original = Path(filepath).read_bytes()
            Path(os.path.join("./temp", f"{os.path.basename(filepath)}.enc")).write_bytes(original)
            raise FileEncryptedException(f"File {filepath} is already encrypted with AES encryption.")

        if len(base64.urlsafe_b64decode(Path(keypath).read_bytes())) == 32:
            return self.encrypt_file_aes(keypath, filepath)

        return self.encrypt_file_fernet(keypath, filepath)

    def decrypt_file(self, keypath: str, filename: str) -> bool:
        """
        Decrypts a file using the keyfile
        :param keypath:  path to the keyfile
        :param filename:  name of the file to decrypt
        :return:
        """

        # VERIFY IF KEYFILE AND FILE EXISTS
        if not os.path.exists(keypath):
            raise FileNotFoundError(f"Keyfile {keypath} does not exist.")

        if not os.path.exists(filename):
            raise FileNotFoundError(f"File {filename} does not exist.")

        if not filename.endswith(".enc"):
            raise FileNotEncryptedException(f"File {filename} is not encrypted.")

        if (not Path(filename).read_bytes().startswith(b"ENC-TERABOXUPLOADERCLI") and not Path(filename).read_bytes().
                startswith(b"ENC-TERABOXUPLOADERCLI-AES")):
            raise FileNotEncryptedException(f"File {filename} is not encrypted with Fernet or AES encryption by "
                                            f"TeraboxUploaderCLI.")

        if len(base64.urlsafe_b64decode(Path(keypath).read_bytes())) == 32:
            return self.decrypt_file_aes(keypath, filename)

        return self.decrypt_file_fernet(keypath, filename)

    def encrypt_file_aes(self, keypath: str, filepath: str) -> bool:
        """
        Encrypts a file using an AES key
        :param keypath:  path to the keyfile
        :param filepath: path to the file to encrypt
        :return:
        """

        # VERIFY IF KEYFILE AND FILE EXISTS
        if not os.path.exists(keypath):
            raise FileNotFoundError(f"Keyfile {keypath} does not exist.")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist.")

        try:
            key = base64.urlsafe_b64decode(Path(keypath).read_bytes())
        except Exception as e:
            raise EncryptFileException(f"Something went wrong when loading keyfile: {e}") from e

        destination = os.path.join("./temp", f"{os.path.basename(filepath)}.enc")

        # OPEN FILE, ENCRYPT AND SAVE
        try:
            with open(filepath, 'rb') as infile, open(destination, 'wb') as outfile:
                outfile.write(b"ENC-TERABOXUPLOADERCLI-AES\n")

                iv = os.urandom(16)
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                encryptor = cipher.encryptor()
                padder = padding.PKCS7(128).padder()
                outfile.write(iv)

                while True:
                    chunk = infile.read(self.chunk_size)
                    if len(chunk) == 0:
                        outfile.write(encryptor.update(padder.finalize()) + encryptor.finalize())
                        break

                    padded_chunk = padder.update(chunk)
                    encrypted_chunk = encryptor.update(padded_chunk)
                    outfile.write(encrypted_chunk)

        except Exception as e:
            raise EncryptFileException(f"Something went wrong when encrypting file: {e}") from e

        return True

    def encrypt_file_fernet(self, keypath: str, filepath: str) -> bool:
        """
        Encrypts a file using a Fernet key
        :param keypath:  path to the keyfile
        :param filepath: path to the file to encrypt
        :return:
        """

        try:
            key = Path(keypath).read_bytes()
        except Exception as e:
            raise EncryptFileException(f"Something went wrong when loading keyfile: {e}") from e

        destination = os.path.join("./temp", f"{os.path.basename(filepath)}.enc")

        # OPEN FILE, ENCRYPT AND SAVE
        try:
            with open(filepath, 'rb') as infile, open(destination, 'wb') as outfile:
                outfile.write(b"ENC-TERABOXUPLOADERCLI\n")

                key = base64.urlsafe_b64encode(key)
                fernet = Fernet(key)
                outfile.write(fernet.encrypt(infile.read()))

        except Exception as e:
            raise EncryptFileException(f"Something went wrong when encrypting file: {e}") from e

        return True

    def decrypt_file_aes(self, keypath: str, filename: str) -> bool:
        """
        Decrypts a file using the keyfile
        :param self: self object of the class
        :param keypath:  path to the keyfile
        :param filename:  name of the file to decrypt
        :return:
        """

        # VERIFY IF KEYFILE AND FILE EXISTS
        if not os.path.exists(keypath):
            raise FileNotFoundError(f"Keyfile {keypath} does not exist.")

        if not os.path.exists(filename):
            raise FileNotFoundError(f"File {filename} does not exist.")

        # VERIFY IF FILE IS ENCRYPTED
        if "enc" not in filename:
            raise FileNotEncryptedException(f"File {filename} is not encrypted.")

        # LOAD KEY
        try:
            key = base64.urlsafe_b64decode(Path(keypath).read_bytes())
        except Exception as e:
            raise DecryptFileException(f"Something went wrong when loading keyfile: {e}") from e

        destination = os.path.join("./temp", f"{os.path.basename(filename)[:-4]}.dec")

        # OPEN FILE, DECRYPT AND SAVE
        try:
            with open(filename, 'rb') as infile, open(destination, 'wb') as outfile:
                infile.readline()
                iv = infile.read(16)

                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                unpadder = padding.PKCS7(128).unpadder()

                while True:
                    chunk = infile.read(self.chunk_size)
                    if len(chunk) == 0:
                        outfile.write(unpadder.finalize())
                        break

                    decrypted_chunk = unpadder.update(decryptor.update(chunk))
                    outfile.write(decrypted_chunk)

        except Exception as e:
            raise DecryptFileException(f"Something went wrong when decrypting file: {e}") from e

        return True

    def decrypt_file_fernet(self, keypath: str, filename: str) -> bool:
        """
        Decrypts a file using the keyfile
        :param self:     self object of the class
        :param keypath:  path to the keyfile
        :param filename: name of the file to decrypt
        :return:
        """

        # VERIFY IF KEYFILE AND FILE EXISTS
        if not os.path.exists(keypath):
            raise FileNotFoundError(f"Keyfile {keypath} does not exist.")

        if not os.path.exists(filename):
            raise FileNotFoundError(f"File {filename} does not exist.")

        # VERIFY IF FILE IS ENCRYPTED
        if "enc" not in filename:
            raise FileNotEncryptedException(f"File {filename} is not encrypted.")

        # LOAD KEY
        try:
            key = Path(keypath).read_bytes()
        except Exception as e:
            raise DecryptFileException(f"Something went wrong when loading keyfile: {e}") from e

        destination = os.path.join("./temp", f"{os.path.basename(filename)[:-4]}.dec")

        # OPEN FILE, DECRYPT AND SAVE
        try:
            with open(filename, 'rb') as infile, open(destination, 'wb') as outfile:
                infile.readline()
                key = base64.urlsafe_b64encode(key)
                fernet = Fernet(key)
                outfile.write(fernet.decrypt(infile.read()))
        except InvalidToken as exc:
            raise DecryptFileException("Invalid key or file") from exc

        except Exception as e:
            raise DecryptFileException(f"Something went wrong when decrypting file: {e}") from e

        return True
