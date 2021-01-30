import os

from mock import patch
import pytest

from vlt.app import (
    _add_to_db,
    _remove_from_db,
    _get_from_db,
    _edit_db
)
from vlt.encryption import Rosetta
from vlt.storage import DataBase
from vlt.settings import Settings

from .base import Expectation

class MockSession:
    def __init__(self) -> None:
        self.db = DataBase(
            name="test.db", 
            settings=Settings(prefix="test")
        ).init_db()
        self.rosetta = Rosetta(password='password', salt="ThisIsSalt")
        self.settings = self.db.settings
        self.df = self.db.get().applymap(self.rosetta.decrypt)

@pytest.fixture
def session():
    mock_session = MockSession()
    yield mock_session
    os.unlink(mock_session.db.name)
    os.unlink(mock_session.settings.name)

@pytest.fixture
def full_session():
    mock_session = MockSession()
    for i in range(10):
        _add_to_db(mock_session, **{'-s': f'source_{i}', '-u': f'username_{i}', '-p': f'password_{i}'})
    yield mock_session
    os.unlink(mock_session.db.name)
    os.unlink(mock_session.settings.name)

class TestOperations:
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

    def test_edit(self, full_session, capsys):
        _edit_db(full_session, **{
            '-i': '4', '-s': "edit_source_4", 
            '-u': "edit_username_4", '-p': "edit_password_4"}
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
        

