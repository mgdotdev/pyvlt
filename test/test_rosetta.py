import pytest
from vlt.encryption import Rosetta

class TestRosetta:
    def test_encryption(self):
        expected = 'testing one two three'
        stone = Rosetta(key="TestPassword", salt="ThisIsSalt")
        encrypted = stone.encrypt(expected)
        actual = stone.decrypt(encrypted)
        assert actual == expected
