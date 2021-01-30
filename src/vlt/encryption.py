import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def derive_key(password, salt):
    password = str.encode(password)
    salt = str.encode(salt)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA512(),length=32,salt=salt,iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

class Rosetta:
    def __init__(self, password, salt):
        self.rosetta = Fernet(derive_key(password, salt))

    def encrypt(self, text):
        text = str.encode(text)
        return self.rosetta.encrypt(text).decode()

    def decrypt(self, text):
        text = self.rosetta.decrypt(text.encode())
        return text.decode()
