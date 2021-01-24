import base64
import json
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def derive_key(password):

    password = str.encode(password)
    salt = b'7\xe4\xf6\xa0\xb9\n\x89\xbaK\xee\x046\x06O\xcd\x90'

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )

    key = base64.urlsafe_b64encode(kdf.derive(password))

    return key

class Rosetta:
    def __init__(self, password):
        self.key = derive_key(password)
        self.rosetta = Fernet(self.key)

    def encrypt(self, text):
        text = str.encode(text)
        return self.rosetta.encrypt(text).decode()

    def decrypt(self, text):
        text = self.rosetta.decrypt(text.encode())
        return text.decode()
