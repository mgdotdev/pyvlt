import os

import pytest

from vlt.storage import DataBase

class TestDataBase:
    def test_meta_operations(self):
        db = DataBase().create_db()
        assert db._get_table_names() == ['storage']
        db._drop_table('storage')
        assert db._get_table_names() == []
        db._reset_db()
        assert db._get_table_names() == ['storage']
        os.unlink(db.name)
