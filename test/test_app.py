import os
import string
import pandas as pd
import pyperclip
import time

from mock import patch
import pytest

from vlt.app import (
    Session,
    _add_to_db,
    _confirm,
    _consume_csv,
    _copy_to_clipboard,
    _dump_to_csv, 
    _edit_db,
    _get_from_db,
    _get_index,
    _make_db_entry,
    _remove_from_db,
    _reset
)

from .base import Expectation, Fixture

@pytest.fixture
def session():
    mock_session = Session(key="TestKey", prefix="test", name="test.db")
    yield mock_session
    os.unlink(mock_session.db.name)
    os.unlink(mock_session.settings.name)

@pytest.fixture
def full_session():
    mock_session = Session(key="TestKey", prefix="test", name="test.db")
    for i in range(10):
        _add_to_db(mock_session, **{'-s': f'source_{i}', '-u': f'username_{i}', '-p': f'password_{i}'})
    yield mock_session
    os.unlink(mock_session.db.name)
    os.unlink(mock_session.settings.name)


class TestAdd:
    def test_add(self, session):
        with patch('builtins.input', return_value="test"):
            _add_to_db(session)
        actual = session.db.get().applymap(session.rosetta.decrypt).values.tolist()
        assert actual == [['test', 'test', 'test']]

    def test_add_with_kwargs(self, session):
        kwargs = {'-s': 'test_source', '-u': 'test_user', '-p': 'test_password'}
        with patch('builtins.input', return_value="test"):
            _add_to_db(session, **kwargs)
        actual = session.db.get().applymap(session.rosetta.decrypt).values.tolist()
        expected = Expectation("test_add_with_kwargs.json")
        assert actual == expected.data

    def test_add_with_some_kwargs(self, session):
        kwargs = {'-s': 'test_source', '-u': 'test_user'}
        with patch('builtins.input', return_value="test"):
            _add_to_db(session, **kwargs)
        actual = session.db.get().applymap(session.rosetta.decrypt).values.tolist()
        expected = Expectation("test_add_with_some_kwargs.json")
        assert actual == expected.data


class TestEdit:
    def test_edit(self, full_session, capsys):
        _edit_db(full_session, **{
            '-i': '4', 
            '-s': "edit_source_4", 
            '-u': "edit_username_4", 
            '-p': "edit_password_4"}
        )
        _get_from_db(full_session, "all", **{'--format': 'h'})
        actual = capsys.readouterr().out
        expected = Expectation("test_edit.txt")
        assert actual == expected.data

    def test_edit_no_index(self, full_session, capsys):
        with patch('builtins.input', return_value="1"):
            _edit_db(full_session, **{
                '-s': "edit_source_1", 
                '-u': "edit_username_1", 
                '-p': "edit_password_1"
            })
        _get_from_db(full_session, "all", **{'--format': 'h'})
        actual = capsys.readouterr().out
        expected = Expectation("test_edit_no_index.txt")
        assert actual == expected.data


class TestGet:
    def test_get_raw(self, full_session, capsys):
        _get_from_db(full_session, "raw", **{'--format': 'h'})
        actual = capsys.readouterr().out
        expected = Expectation("test_get_raw.txt")
        assert actual.split('\n')[:4] == expected.data.split('\n')[:4]

    def test_get_all(self, full_session, capsys):
        _get_from_db(full_session, "all", **{'--format': 'h'})
        actual = capsys.readouterr().out  
        expected = Expectation("test_get_all.txt")
        assert actual == expected.data

    def test_get_source(self, full_session, capsys):
        _get_from_db(full_session, **{'--source': "source_3", "--format": 'h'})   
        actual = capsys.readouterr().out  
        expected = Expectation("test_get_source.txt")
        assert actual == expected.data

    def test_get_username(self, full_session, capsys):
        _get_from_db(full_session, **{'--username': "username_3", "--format": 'h'})   
        actual = capsys.readouterr().out  
        expected = Expectation("test_get_username.txt")
        assert actual == expected.data

    def test_get_password(self, full_session, capsys):
        _get_from_db(full_session, **{'--password': "password_3", "--format": 'h'})   
        actual = capsys.readouterr().out  
        expected = Expectation("test_get_password.txt")
        assert actual == expected.data


class TestCopy:
    @property
    def _df(self):
        return pd.DataFrame(
            {
                'source':["source_0"], 
                'username': ["username_0"], 
                'password': ["password_0"]
            }
        )
    def test_copy(self, full_session):
        with patch('builtins.input', return_value=""):
            _copy_to_clipboard(full_session, self._df, 's', 'v')
        assert pyperclip.paste() == ""

    def test_copy_time(self, full_session):
        start_time = time.time()
        with patch('builtins.input', return_value=""):
            _copy_to_clipboard(full_session, self._df, 's', 'v', **{"--time": "3"})
        assert time.time() - start_time > 3
        assert pyperclip.paste() == ""


class TestMake:
    def test_make(self, session):
        _make_db_entry(session, **{"--source": "test", "--username": "test"})
        actual = session.db.get().applymap(session.rosetta.decrypt).values.tolist()
        assert actual[0][0:2] == ["test", "test"]

    def test_make_omit(self, session):
        omits = string.ascii_letters
        _make_db_entry(session, **{
            "--length": "42", 
            "--source": "test", 
            "--username": "test",
            "--omit": omits
        })
        actual = session.db.get().applymap(session.rosetta.decrypt).values.tolist()
        assert actual[0][0:2] == ["test", "test"]
        assert all(s not in omits for s in actual[0][2])
        assert len(actual[0][2]) == 42


class TestRemove:
    def test_remove(self, full_session):
        _remove_from_db(full_session, **{'--index': '3'})
        actual = full_session.db.get().applymap(full_session.rosetta.decrypt).values.tolist()
        expected = Expectation("test_remove.json")
        assert actual == expected.data

    def test_remove_no_index(self, full_session):
        with patch('builtins.input', return_value="3"):
             _remove_from_db(full_session)
        actual = full_session.db.get().applymap(full_session.rosetta.decrypt).values.tolist()
        expected = Expectation("test_remove_no_index.json")
        assert actual == expected.data


class TestReset:
    def test_reset_key(self, full_session):
        table_salt = full_session.db.table_salt
        initial_salt = full_session.db.get_salt(full_session.db.table)
        with patch('builtins.input', return_value="y"):
            _reset(full_session, "key", **{"-k": "NewTestKey"})
        actual = full_session.db.get().applymap(full_session.rosetta.decrypt).values.tolist()
        expected = Expectation("session_full.json")
        assert table_salt == full_session.db.table_salt
        assert initial_salt != full_session.db.get_salt(full_session.db.table)
        assert actual == expected.data

    def test_reset_table(self, full_session):
        initial_salt = full_session.db.table_salt
        with patch('builtins.input', return_value="y"):
            _reset(full_session, "table")
        actual = full_session.db.get().applymap(full_session.rosetta.decrypt).values.tolist()
        expected = Expectation("session_empty.json")
        assert initial_salt == full_session.db.table_salt
        assert actual == expected.data
        
    def test_reset_db(self, full_session):
        initial_salt = full_session.db.table_salt
        with patch('builtins.input', return_value="y"):
            _reset(full_session, "db")
        actual = full_session.db.get().applymap(full_session.rosetta.decrypt).values.tolist()
        expected = Expectation("session_empty.json") 
        assert initial_salt != full_session.db.table_salt
        assert actual == expected.data

    def test_reset_app(self):
        session = Session(key="TestKey", prefix="test", name="test.db")
        settings = session.settings._read()
        with patch('builtins.input', return_value="y"):
            _reset(session, "app")
        assert os.path.isfile(settings['name']) is False


class TestCSVio:
    def test_consume(self, session):
        fixture = Fixture("unencrypted_dataset.txt")
        expected = Expectation("session_full.json")
        _consume_csv(session, fixture.name)
        actual = session.db.get().applymap(session.rosetta.decrypt).values.tolist()
        assert actual == expected.data
    
    def test_dump(self, full_session):
        expected = Fixture("unencrypted_dataset.txt")
        temp = Expectation("unencrypted_dataset.txt")
        _dump_to_csv(full_session, temp.name)
        actual = Expectation("unencrypted_dataset.txt")
        assert actual.data == expected.data
        

class TestMisc:
    def test_print_df(self, full_session, capsys):
        _get_from_db(full_session, **{'--password': "password_3", "--format": 'h'})
        _get_from_db(full_session, **{'--password': "password_3", "--format": 'v'})
        _get_from_db(full_session, **{'--password': "password_3", "--format": 'df'})
        actual = capsys.readouterr().out  
        expected = Expectation("test_print_df.txt")
        assert actual == expected.data

    def test_confirm(self):
        with patch('builtins.input', return_value="y"):
            assert _confirm()

    def test_get_index(self, session):
        with patch('builtins.input', return_value="1"):
            assert _get_index(session, "test")