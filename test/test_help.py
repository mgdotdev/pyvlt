import pytest

from vlt.help_menu import HelpMenu

from .base import Expectation

@pytest.fixture(scope="session")
def menu():
    menu = HelpMenu()
    yield menu


class TestHelp:
    def test_get_help(self, menu, capsys):
        cmd = ""
        menu.get(cmd)
        actual = capsys.readouterr().out
        expected = Expectation("test_get_help.txt")
        assert actual == expected.data

    def test_get_cmd(self, menu, capsys):
        cmd = "edit"
        menu.get(cmd)
        actual = capsys.readouterr().out
        expected = Expectation("test_get_edit.txt")
        assert actual == expected.data