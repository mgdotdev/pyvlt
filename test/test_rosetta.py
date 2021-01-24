import pytest
from vlt.encryption import Rosetta

class TestRosetta:
    def test_encryption(self):
        password = 'password'
        expected = 'testing one two three'
        stone = Rosetta(password)
        encrypted = stone.encrypt(expected)
        actual = stone.decrypt(encrypted)
        assert actual == expected
