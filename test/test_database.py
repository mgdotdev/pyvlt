import os
from sys import prefix
from numpy.lib.function_base import sort_complex

import pandas as pd

import pytest

from vlt.settings import Settings
from vlt.storage import DataBase
from vlt.encryption import Rosetta

@pytest.fixture
def settings_and_database():
    settings = Settings(prefix="test")
    database = DataBase(name="test.db", key="TestKey", settings=settings)
    yield settings, database
    os.unlink(database.name)
    os.unlink(settings.name)    


class TestDataBase:
    def test_default_tables(self, settings_and_database):
        _, database = settings_and_database
        table_names = database._table_names
        assert "salts" in table_names
        table_names.remove("salts")
        assert all(name.startswith("table_") for name in table_names)

    def test_reset(self, settings_and_database):
        _, database = settings_and_database
        database._reset_db()
        table_names = database._table_names
        assert "salts" in table_names
        table_names.remove("salts")
        assert all(name.startswith("table_") for name in table_names)        


class TestDatabaseEncryption:
    def test_database_io(self, settings_and_database):
        stone = Rosetta(key='password', salt="ThisIsSalt") 
        _, database = settings_and_database
        test_sources = ['facebook', 'google', 'microsoft']
        expected = [
            [
                stone.encrypt(test_sources[i%len(test_sources)]), 
                stone.encrypt(f'user_{i}'), 
                stone.encrypt(f'password_{i}')
            ] 
            for i in range(12)
        ]
        database.add_list_of_lists(expected)
        actual = database.get().values.tolist()
        assert actual == expected
