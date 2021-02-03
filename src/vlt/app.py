import functools
from getpass import getpass
import json
import os
import random
import shutil
import secrets
import string
import time
import uuid

import pandas as pd
import pyperclip

from .cmd_reader import reader
from .encryption import Rosetta
from .storage import DataBase
from .settings import Settings
from .constants import *

def main():
    cmd, args, kwargs = reader()
    if cmd in {'-i', '--interactive'}:
        Session.interactive()
    else:
        Session.static(cmd, args, kwargs)

def _add_to_db(self, *args, **kwargs):
    source = (
        kwargs.get('-s') or kwargs.get('--source') 
        or input('\nspecify source:\n$ ')
    )
    username = (
        kwargs.get('-u') or kwargs.get('--username') 
        or input('\nspecify username:\n$ ')
    )
    password = (
        kwargs.get('-p') or kwargs.get('--password') 
        or input('\nspecify password:\n$ ')
    )
    if all(x=='' for x in (source, username, password)):
        raise ValueError(
            "<add> requires a source, username, and/or password to enter"
        )
    self.db.add(
        source=self.rosetta.encrypt(source), 
        username=self.rosetta.encrypt(username), 
        password=self.rosetta.encrypt(password)        
    )
    df = self.db.get().applymap(self.rosetta.decrypt)
    self.df = df
    
def _archive(*args, **kwargs):
    if args:
        filename = args[0]
    else:
        filename = (
            kwargs.get('-n') or kwargs.get('--name') 
            or input('\nplease enter a file name:\n$ ')
        )
    if not filename.endswith('.db'):
        filename += '.db'
    settings = Settings()
    archive_file = os.path.join(os.path.dirname(settings["name"]), filename)
    os.rename(settings["name"], archive_file)
    settings.archive(archive_file)
    settings._write()

def _confirm(message="are you sure? This can not be undone."):
    if not message.endswith(" [y/n]\n$ "):
        message += " [y/n]\n$ "
    confirm = input(message)
    if confirm == 'y':
        return True
    return False

def _consume_csv(self, *args, **kwargs):
    path = args[0] or kwargs.get('-p') or kwargs.get('--path') or input(
        '\nplease enter a filepath to the consumable csv:\n$ '
    )
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError("path does not represent a valid file.")
    df = self.db.get().applymap(self.rosetta.decrypt)
    new_df = pd.read_csv(path)
    df = df.append(new_df, ignore_index=True)
    self.db.update_db(df.applymap(self.rosetta.encrypt))
    self.df = df

def _copy_to_clipboard(self, df, cp, format_option, **kwargs):
    index = df.index.values.tolist()
    if len(index) > 1:
        print(
            "search parameters are ambiguous. "
            "Consider using the index when copying.\n"
        )
        if _confirm("display results of the search?"):
            _print_df(df, format_option)
    else:
        cache_time = kwargs.get("-t") or kwargs.get("--time") or self.settings["cache_time"]
        mapping = {
            "s": "source",
            "u": "username",
            "p": "password"
        }
        if 'd' in cp:
            _print_df(df, format_option)
        cp = cp.replace("d", "")
        for item in cp:
            pyperclip.copy(df.loc[index[0], mapping[item]])
            if cache_time:
                for t in reversed(range(int(float(cache_time)))):
                    print(
                        f"{mapping[item]} copied to clipboard."
                        " {:>5} seconds till next...".format(t), 
                        end='\r'
                    )
                    time.sleep(1)
                print("")
            else:
                input(
                    f"{mapping[item]} copied to clipboard. "
                    f"Press Enter to continue...\n"
                )
        pyperclip.copy("")

def _dump_to_csv(self, *args, **kwargs):
    path = args[0] or kwargs.get('-p') or kwargs.get('--path') or input(
        '\nplease enter a filepath to copy the vlt db to:\n$ '
    )
    if not path.endswith('.csv'):
        path += '.csv'
    path = os.path.normpath(path)
    if not os.access(os.path.dirname(path), os.W_OK):
        raise NotADirectoryError("path is not a valid directory.")
    df = self.db.get().applymap(self.rosetta.decrypt)
    df.to_csv(path, index=False)

def _edit_db(self, *args, **kwargs):
    index = (
        kwargs.get('-i') 
        or kwargs.get('--index') 
        or _get_index(self, "edit")
    )
    index = int(index)
    df = self.db.get().applymap(self.rosetta.decrypt)
    source = kwargs.get('-s') or kwargs.get('--source')
    username = kwargs.get('-u') or kwargs.get('--username')
    password = kwargs.get('-p') or kwargs.get('--password')
    if all(x==None for x in (source, username, password)):
        source = input('\nspecify new source. (Empty strings are ignored):\n$ ')
        username = input('\nspecify new username. (Empty strings are ignored):\n$ ')
        password = input('\nspecify new password. (Empty strings are ignored):\n$ ')
    if all(x=="" for x in (source, username, password)):
        print("No entries were selected to edit.")
        return df
    if source:
        df.loc[index, "source"] = source
    if username:
        df.loc[index, "username"] = username
    if password:
        df.loc[index, "password"] = password
    self.db.update_db(df.applymap(self.rosetta.encrypt))
    self.df = df
    
def _export_db(*args, **kwargs):
    path = args[0] or kwargs.get('-p') or kwargs.get('--path') or input(
        '\nplease enter a filepath to copy the vlt db to:\n$ '
    )
    if not path.endswith('.db'):
        path += '.db'
    path = os.path.normpath(path)
    settings = Settings()
    if not os.access(os.path.dirname(path), os.W_OK):
        raise NotADirectoryError("path is not to a valid directory.")
    shutil.copy2(settings["name"], path)       

def _get_from_db(self, *args, **kwargs):
    format_option = (
        kwargs.get("-fmt") or kwargs.get("--format") 
        or self.settings["print_format"]
    )

    if args == () and not any(
        c in kwargs.keys() for c in (
            '-i', '--index', '-s', '--source', 
            '-u', '--username', '-p', '--password'
        )
    ):
        args, kwargs = _request_search_terms()
    df = self.db.get()
    if "raw" in args:
        return _print_df(df, format_option)

    df = df.applymap(self.rosetta.decrypt)
    if "all" in args:
        return _print_df(df, format_option)

    index = kwargs.get('-i') or kwargs.get('--index')
    source = kwargs.get('-s') or kwargs.get('--source')
    username = kwargs.get('-u') or kwargs.get('--username')
    password = kwargs.get('-p') or kwargs.get('--password')
    if all(x==None for x in (index, source, username, password)):
        raise ValueError(
            "<get> requires an index, source, username, and/or password to search against."
        )
    if index:
        df = df.loc[df.index == df.index[int(index)]]
    if source:
        df = df.loc[df['source'].str.contains(source)]
    if username:
        df = df.loc[df['username'] == username]
    if password:
        df = df.loc[df['password'] == password]
    
    cp = (
        kwargs.get('-cp') 
        or kwargs.get("--clip") 
        or self.settings['clipboard_settings']
    )
    if cp:
        _copy_to_clipboard(self, df, cp, format_option, **kwargs)
    else:
        _print_df(df, format_option)

def _get_index(self, action):
    index = input(
        f"\npass the index value of the entry to {action}."
        f"\nif unknown, press enter to search.\n$ "
    )
    if not index:
        _get_from_db(self)
        index = _get_index(self, action)
    return index

def _link_db(*args, **kwargs):
    if args:
        path = args[0]
    else:
        path = (
            kwargs.get('-f') or kwargs.get('--file') 
            or kwargs.get("-a") or kwargs.get("--archive") 
            or input(
                'please enter a filepath to the external vlt db, '
                'or an archive index value:\n'
                '$ '
            )
        )
    db = DataBase(key='temp')
    if not db.settings["archives"]:
        pass
    elif path in db.settings["archives"].keys():
        path = db.settings["archives"][path]
    if not os.path.isfile(path):
        raise FileNotFoundError(f'argument passed ({path}) is not a valid file.')
    if not path.endswith('.db'):
        raise FileNotFoundError(f'argument passed ({path}) should be of filetype .db')
    if db.settings["name"]:
        db.settings.archive(db.settings["name"])
        db.settings.update({"name": path})
    else:
        db.settings.update({"name": path})
    if not db.check_table_exists('salts'):
        raise LookupError(f"passed .db file ({path}) doesn't have <salts> table")
    if not db.table_salt:
        raise LookupError(f"passed .db file ({path}) doesn't have a <table_salt> encryption token")
    db.settings._write()
    
def _list_db(*args, **kwargs):
    settings = Settings()
    if "archives" in args:
        archives = settings["archives"]
        if type(archives) == dict:
            for key, value in archives.items():
                print("{:>5}: {}".format(int(key), value))
        else:
            print('None')
    elif "name" in args:
        print("    -  " + settings["name"])
    elif "cmd" in args:
        print(json.dumps(COMMAND_MAPPING, indent=2, sort_keys=True))
    else:
        print(json.dumps(settings.settings, indent=2, sort_keys=True))

def _make_db_entry(self, *args, **kwargs):
    password_length = int(
        kwargs.get("-l") 
        or kwargs.get("--length") 
        or self.settings["default_password_length"] 
        or DEFAULT_PASSWORD_LENGTH
    )
    omits = (
        kwargs.get("-o") 
        or kwargs.get("--omit") 
        or self.settings["default_omit_chars"]
        or ""
    )
    mode = (
        kwargs.get("-v") 
        or kwargs.get("--via") 
        or self.settings["default_make_mode"]
        or "random"
    )
    kwargs.update({"--password": _make_password(password_length, mode, omits)})
    _add_to_db(self, *args, **kwargs)
    kwargs.update({'--index': -1})
    _get_from_db(self, *args, **kwargs)
    
def _make_password(password_length, mode, omits, iterations=0):
    if iterations > MAX_PASSWORD_ITERATIONS:
        raise RecursionError(
            f"attempted password could not be made "
            f"after {MAX_PASSWORD_ITERATIONS} iteration "
            f"attempts. Consider adjusting the password "
            f"length, the mode, or the omit characters."
        )
    elif mode == "uuid":
        return str(uuid.uuid4())
    elif mode == "hex":
        return secrets.token_hex(password_length)

    if mode == "random":
        mode += 'loweruppernumericpunctuation'
    elif 'alpha' in mode:
        mode += 'lowerupper'

    char_types = []
    if 'lower' in mode:
        char_types.append(string.ascii_lowercase)
    if 'upper' in mode:
        char_types.append(string.ascii_uppercase)
    if 'numeric' in mode:
        char_types.append(string.digits)
    if 'punctuation' in mode:
        char_types.append(string.punctuation)

    for index, types in enumerate(char_types):
        char_types[index] = functools.reduce(
            lambda t, i: t.replace(i, ""), [types, *omits]
        )
    char_types = [t for t in char_types if t != '']
    chars_string = "".join(char_types)
    result = "".join(
        [random.choice(char) for char in char_types] + 
        [random.choice(chars_string)
        for _ in range(password_length - len(char_types))]
    )[:password_length]
    return result

def _open_ipython(self):
    from IPython import embed
    print('\nvlt objects are callable through `self`.\n')
    embed()

def _print_df(df, option=None):
    if not option or option == 'df':
        print('\n', df, '\n')
        return
    indexes = [str(x) for x in df.index.tolist()]
    df = df.values.tolist()
    if option == "v":        
        if len(df) == 0:
            print("\nThe query produced zero results.\n")
        else:
            print('\n')
            for index, item in zip(indexes, df):
                print(
                    f"{index}.\n"
                    f"  SOURCE: {item[0]}\n"
                    f"USERNAME: {item[1]}\n"
                    f"PASSWORD: {item[2]}\n"
                )
    elif option == 'h':
        print('\n')
        max_lengths = [
            max(len(item) for item in column) for column in 
            [indexes + TABLE_HEADERS[:1]] + list(zip(*df, TABLE_HEADERS[1:]))
        ]

        print("  ".join([
            f"{h}{' ' * (l - len(h))}" 
            for l, h in zip(max_lengths, TABLE_HEADERS)
        ]))
        print("  ".join(["-" * l for l in max_lengths]))
        for index, x in zip(indexes, df):
            x = [index] + x
            print("  ".join([
                item + (" " * (length - len(item))) 
                for item, length in zip(x, max_lengths)
            ]))
        print('\n')

def _remove_from_db(self, *args, **kwargs):
    if "all" in args:
        return _reset(self, "table")
    index = kwargs.get('-i') or kwargs.get('--index') or _get_index(self, "remove")
    df = self.df[self.df.index != self.df.index[int(index)]]
    self.db.update_db(df.applymap(self.rosetta.encrypt))
    self.df = df
    
def _request_search_terms():
    search_term = input(
        '\nspecify search term(s):\n'
        ' 1) index\t 3) username\n'
        ' 2) source\t 4) password\n'
        '$ '
    )
    args, kwargs = [], {}
    if search_term == "":
        args.append("all")

    elif search_term == "raw":
        args.append("raw")

    if any(c in search_term for c in ('1', 'source')):
        kwargs.update({'--index': input('\nspecify index:\n$ ')})

    if any(c in search_term for c in ('2', 'source')):
        kwargs.update({'--source': input('\nspecify source:\n$ ')})

    if any(c in search_term for c in ('3', 'username')):
        kwargs.update({'--username': input('\nspecify username:\n$ ')})

    if any(c in search_term for c in ('4', 'password')):
        kwargs.update({'--password': input('\nspecify password:\n$ ')})
    return args, kwargs

def _reset(self, *args, **kwargs):
    if len(args) == 0:
        print('no reset parameter specified.')
    elif "key" in args:
        new_key = kwargs.get('-k') or kwargs.get('--key') or getpass('new key:\n$ ')
        if _confirm():
            self.db._drop_table()
            self.db = DataBase(key=new_key, settings=self.settings)
            self.rosetta = Rosetta(new_key, self.db.get_salt(self.db.table))
            self.db.update_db(self.df.applymap(self.rosetta.encrypt))
            self.df = self.db.get().applymap(self.rosetta.decrypt)
            return True
    elif "table" in args and _confirm():
        self.db._drop_table()
        self.db.init_db()
        self.df = self.db.get().applymap(self.rosetta.decrypt)
        return True        
    elif "db" in args and _confirm():
        print('\ndeleting all data from .db\n')
        self.db._reset_db()
        return False
    elif "app" in args and _confirm():
        print('\ndeleting all internal .db files and removing config.\n')
        shutil.rmtree(os.path.join(HERE, 'db'))
        os.unlink(self.settings.name)
        return False
    else:
        print('passed argument does not match any reset protocols.')
    print('aborting...')
    return True

def _settings(*args, **kwargs):
    settings = Settings()
    print_format = kwargs.get("-fmt") or kwargs.get("--format")
    if print_format in PRINT_FORMAT_SETTINGS:
        settings.update({"print_format": print_format})
    default_password_length = kwargs.get("-l") or kwargs.get("--length")
    if default_password_length:
        if default_password_length == "None":
            settings.pop("default_password_length")
        else:
            settings.update({"default_password_length": default_password_length})
    omits = kwargs.get("-o") or kwargs.get("--omit")
    if omits:
        if omits == 'None':
            settings.pop("default_omit_chars")
        else:
            settings.update({"default_omit_chars": omits})
    via = kwargs.get("-v") or kwargs.get("--via")
    if via:
        if via == "None":
            settings.pop("default_make_mode")
        else:
            settings.update({"default_make_mode": via})
    settings._write()
    
def _try_again(self):
    print('\naction not understood. Please try again, or type `exit` or `q` to quit\n')
    self.main()


class Session:
    def __init__(self, key=None, prefix=None, name=None):
        self.settings = Settings(prefix=prefix)
        self.db = DataBase(name=name, key=key, settings=self.settings)
        self.rosetta = Rosetta(key=key, salt=self.db.get_salt(self.db.table))
        self.df = self.db.get().applymap(self.rosetta.decrypt)

    def main(self):
        action = self._main_action()

        if action in ('get', '1'):
            _get_from_db(self)
            self.main()
        elif action in ('add', '2'):
            _add_to_db(self)
            self.main()
        elif action in ('make', '3'):
            _make_db_entry(self)
            self.main()
        elif action in ('edit', '4'):
            _edit_db(self)
            self.main()
        elif action in ("remove", '5'):
            _remove_from_db(self)
            self.main()
        elif action in ('settings', '6'):
            self.settings_menu()
        elif action in ('exit', 'q', '7'):
            print('bye!\n')
        elif action == 'ipython':
            _open_ipython(self)
            self.main()
        else:
            _try_again(self)


    def settings_menu(self):
        settings_action = self._settings_action()

        if settings_action in ('1', 'reset key'):
            new_key = getpass('new key:')
            _reset(self, 'key', **{'--key': new_key})
            self.main()
        elif settings_action in ('2', 'reset table'):
            _reset(self, 'table')
            self.main()
        elif settings_action in ('3', 'link db'):
            _link_db()
            print("restarting...")
            Session.interactive()
        elif settings_action in ('4', 'list db path'):
            _list_db('name')
            self.main()
        elif settings_action in ('5', 'list archives'):
            _list_db('archives')
            self.main()
        elif settings_action in ('6', 'consume csv'):
            _consume_csv(self)
            self.main()
        elif settings_action in ('7', 'dump db'):
            _dump_to_csv(self)
            self.main()
        elif settings_action in ('8', 'export db'):
            _export_db()
            self.main()
        elif settings_action in ('9', 'archive db'):
            _archive()
            print("restarting...")
            Session.interactive()

        elif settings_action == "RESET_DB":
            if _reset(self, "db"):
                self.main()
            else:
                print("TERMINATING")
        elif settings_action == "RESET_APP":
            if _reset(self, "app"):
                self.main()
            else:
                print("TERMINATING")
        elif settings_action in ("q", "exit"):
            print('bye!\n')
        else:
            _try_again(self)

    @staticmethod
    def interactive():
        key = getpass('Please enter your vlt key:\n$ ')
        self = Session(key)
        self.main()

    @staticmethod
    def static(cmd, args, kwargs):

        if cmd in ('-l', 'lnk', 'link'):
            return _link_db(*args, **kwargs)

        if cmd in ('-ex', 'exp', 'export'):
            return _export_db(*args, **kwargs)

        if cmd in ('-ls', 'ls', 'list'):
            return _list_db(*args, **kwargs)

        if cmd in ('-ar', 'archive'):
            return _archive(*args, **kwargs)

        if cmd in ('-s', 'set', 'settings'):
            return _settings(*args, **kwargs)

        key = kwargs.get('-k') or kwargs.get("--key")
        if not key:
            key = getpass('Please enter your vlt key:\n$ ')
        self = Session(key)

        if cmd in ('-g', 'get'):
            return _get_from_db(self, *args, **kwargs)

        elif cmd in ('+', '-a', 'add'):
            return _add_to_db(self, *args, **kwargs)

        elif cmd in ('-m', 'mk', 'make'):
            return _make_db_entry(self, *args, **kwargs)

        elif cmd in ('-c', 'consume'):
            return _consume_csv(self, *args, **kwargs)

        elif cmd in ('-d', "dump"):
            return _dump_to_csv(self, *args, **kwargs)

        elif cmd in ('-e', 'edit'):
            return _edit_db(self, *args, **kwargs)

        elif cmd in ('-', '-rm', 'rm', 'remove'):
            return _remove_from_db(self, *args, **kwargs)

        elif cmd in ('-rs', 'reset'):
            return _reset(self, *args, **kwargs)

        elif cmd == 'ipython':
            _open_ipython(self)
        
        else:
            print("command not understood, no action taken.\n")

    def _main_action(self):
        return input(
            '\nspecify action:\n'
            ' 1) get   3) make   5) remove   7) exit\n'
            ' 2) add   4) edit   6) settings\n'
            '$ '
        )

    def _settings_action(self):
        return input(
            '\nselect option:\n'
            ' 1) reset key    4) list db path   7) dump db\n'
            ' 2) reset table  5) list archives  8) export db\n'
            ' 3) link db      6) consume csv    9) archive db\n'
            '$ '
        )