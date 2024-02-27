import os.path

from cryptography.fernet import Fernet


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
        :param keyfile:
        :return:
        """
        try:
            key = Fernet.generate_key()
            with open(keyfile, 'wb') as filekey:
                filekey.write(key)
        except Exception as e:
            raise GenerateKeyException(e)
        return True

    @staticmethod
    def encrypt_file(keypath: str, sourcefil: str, filename: str) -> bool:
        """
        Encrypts a file using the keyfile
        :param keypath:  path to the keyfile
        :param sourcefil:  path to the file to encrypt
        :param filename:  name of the file to encrypt
        :return:
        """
        if not os.path.exists(keypath):
            raise EncryptFileException(f"Keyfile {keypath} does not exist.")

        if not os.path.exists(os.path.join(sourcefil, filename)):
            raise EncryptFileException(f"File {os.path.join(sourcefil, filename)} does not exist.")

        if "enc" in filename:
            raise FileEncryptedException(f"File {filename} is already encrypted.")

        try:
            with open(keypath, 'rb') as filekey:
                key = filekey.read()
            fernet = Fernet(key)
        except Exception as e:
            raise EncryptFileException(f"Something went wrong when loading keyfile: {e}")

        try:
            with open(os.path.join(sourcefil, filename), 'rb') as file:
                original = file.read()
        except Exception as e:
            raise EncryptFileException(f"Something went wrong when reading file: {e}")

        try:
            encrypted = fernet.encrypt(original)
        except Exception as e:
            raise EncryptFileException(f"Something went wrong when encrypting file: {e}")

        try:
            with open(os.path.join("./temp", f"{filename}.enc"), 'wb') as encrypted_file:
                encrypted_file.write(encrypted)
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
        if not os.path.exists(keypath):
            raise DecryptFileException(f"Keyfile {keypath} does not exist.")

        if not os.path.exists(filename):
            raise DecryptFileException(f"File {filename} does not exist.")

        if "enc" not in filename:
            raise FileNotEncryptedException(f"File {filename} is not encrypted.")

        try:
            with open(keypath, 'rb') as filekey:
                key = filekey.read()
            fernet = Fernet(key)
        except Exception as e:
            raise DecryptFileException(f"Something went wrong when loading keyfile: {e}")

        try:
            with open(filename, 'rb') as enc_file:
                encrypted = enc_file.read()
            decrypted = fernet.decrypt(encrypted)
        except Exception as e:
            raise DecryptFileException(f"Something went wrong when decrypting file: {e}")

        try:
            with open(filename[:-3], 'wb') as dec_file:
                dec_file.write(decrypted)
        except Exception as e:
            raise DecryptFileException(f"Something went wrong when writing decrypted file: {e}")

        return True
