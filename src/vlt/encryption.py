import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def derive_encryption_key(key: str, salt: str) -> bytes:
    key = str.encode(key)
    salt = str.encode(salt)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA512(),length=32,salt=salt,iterations=100000)
    encryption_key = base64.urlsafe_b64encode(kdf.derive(key))
    return encryption_key

class Rosetta:
    def __init__(self, key: str, salt: str):
        self.rosetta = Fernet(derive_encryption_key(key, salt))

    def encrypt(self, text: str) -> bytes:
        text = str.encode(text)
        return self.rosetta.encrypt(text).decode()

    def decrypt(self, text: bytes) -> str:
        text = self.rosetta.decrypt(text.encode())
        return text.decode()
