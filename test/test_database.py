import os
from sys import prefix
from numpy.lib.function_base import sort_complex

import pandas as pd

import pytest

from vlt.settings import Settings
from vlt.storage import DataBase
from vlt.encryption import Rosetta


class TestDataBase:
    def test_meta_operations(self):
        settings = Settings(prefix="test")
        db = DataBase(name="test.db", settings=settings).init_db()
        assert sorted(db._table_names) == sorted(['settings', 'table_storage'])
        db._drop_table('table_storage')
        assert db._table_names == ['settings']
        db._reset_db()
        assert db._table_names == sorted(['settings', 'table_storage'])
        os.unlink(db.name)
        os.unlink(settings.name)

class TestDatabaseEncryption:
    def test_rosetta_io(self):
        stone = Rosetta(password='password', salt="ThisIsSalt") 
        db = DataBase().init_db()
        test_sources = ['facebook', 'google', 'microsoft']
        expected = [
            [
                stone.encrypt(test_sources[i%len(test_sources)]), 
                stone.encrypt(f'user_{i}'), 
                stone.encrypt(f'password_{i}')
            ] 
            for i in range(12)
        ]
        db.add_list_of_lists(expected)
        actual = db.get().values.tolist()
        assert actual == expected
        os.unlink(db.name)
