from getpass import getpass
import hashlib
import json
import os
import random
import shutil
import secrets
import string
import uuid

import pandas as pd

from .cmd_reader import reader
from .encryption import Rosetta
from .storage import DataBase
from .settings import Settings

HERE = os.path.dirname(os.path.abspath(__file__))
PRINT_FORMAT_SETTINGS = ['df', 'v', 'h']
TABLE_HEADERS = [' ', 'SOURCE', 'USERNAME', 'PASSWORD']
DEFAULT_PASSWORD_LENGTH = 40
MAX_PASSWORD_ITERATIONS = 500

def main():
    cmd, args, kwargs = reader()
    if cmd in {'-i', '--interactive'}:
        Session._interactive()
    elif cmd in {'-h', '--help'}:
        _help_menu()
    else:
        Session._static(cmd, args, kwargs)

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
    db = DataBase()
    archive_file = os.path.join(os.path.dirname(db.settings["name"]), filename)
    os.rename(db.settings["name"], archive_file)
    db.settings.archive(archive_file)
    db.settings._write()

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

def _dump_to_csv(self, *args, **kwargs):
    path = args[0] or kwargs.get('-p') or kwargs.get('--path') or input(
        '\nplease enter a directory path to copy the vlt db to:\n$ '
    )
    path = os.path.normpath(path)
    if not os.access(os.path.dirname(path), os.W_OK):
        raise NotADirectoryError("path is not a valid directory.")
    df = self.db.get().applymap(self.rosetta.decrypt)
    df.to_csv(path, index=False)

def _edit_db(self, *args, **kwargs):
    index = kwargs.get('-i') or kwargs.get('--index') or _get_index(self, "edit")
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
        '\nplease enter a directory path to copy the vlt db to:\n$ '
    )
    path = os.path.normpath(path)
    db = DataBase()
    if not os.access(os.path.dirname(path), os.W_OK):
        raise NotADirectoryError("path is not a valid directory.")
    shutil.copy2(db.settings["name"], path)       

def _get_from_db(self, *args, **kwargs):
    format_option = (
        kwargs.get("-fmt") or kwargs.get("--format") 
        or self.settings["print_format"]
    )

    if args == () and not any(
        c in kwargs.keys() for c in (
            '-i', '--index', '-s', '--source', '-u', '--username', '-p', '--password'
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

def _help_menu():
    with open(os.path.join(HERE, 'help_text.txt'), 'r') as f:
        print(f.read())

def _link_db(*args, **kwargs):
    if args:
        path = args[0]
    else:
        path = (
            kwargs.get('-f') or kwargs.get('--file') 
            or kwargs.get("-a") or kwargs.get("--archive") 
            or input(
                '\nplease enter a filepath to the external vlt db, '
                'or an archive index value:\n$ '
            )
        )
    db = DataBase()
    if not db.settings["archives"]:
        pass
    elif path in db.settings["archives"].keys():
        path = db.settings["archives"][path]
    if not (os.path.isfile(path) and path.endswith('.db')):
        raise FileNotFoundError('argument passed should be of filetype .db')
    if db.settings["name"]:
        db.settings.archive(db.settings["name"])
        db.settings.update({"name": path})
    else:    
        db.settings.update({"name": path})
    if not db.check_table_exists('settings'):
        raise LookupError("passed .db file doesn't have <settings> table")
    if not db.salt:
        raise LookupError("passed .db file doesn't have a <salt> encryption token")
    db.settings._write()
    

def _list_db(*args, **kwargs):
    db = DataBase()
    if "archives" in args:
        archives = db.settings["archives"]
        if type(archives) == dict:
            for key, value in archives.items():
                print("{:>5}: {}".format(int(key), value))
        else:
            print('None')
    elif "name" in args:
        print("    -  " + db.settings["name"])
    else:
        print(json.dumps(db.settings.settings, indent=2, sort_keys=True))

def _make_db_entry(self, *args, **kwargs):
    password_length = int(kwargs.get("-l") or kwargs.get("--length") or DEFAULT_PASSWORD_LENGTH)
    mode = kwargs.get("-v") or kwargs.get("--via") or "random"
    omits = kwargs.get("-o") or kwargs.get("--omit") or ""
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
        gen = str(uuid.uuid4())
    elif mode == "hex":
        gen = secrets.token_hex(password_length)
    else:
        char_types = (
            string.ascii_lowercase, string.ascii_uppercase, 
            string.digits, string.punctuation
        )
        chars_string = "".join(char_types)
        gen = "".join(
            [random.choice(char) for char in char_types] + 
            [random.choice(chars_string) 
            for _ in range(password_length - len(char_types))]
        )[:password_length]
    if any(c in gen for c in omits):
        return _make_password(password_length, mode, omits, iterations=iterations+1)
    return gen

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
    index = kwargs.get('-i') or kwargs.get('--index') or _get_index(self, "remove")
    df = self.df[self.df.index != self.df.index[int(index)]]
    self.db.update_db(df.applymap(self.rosetta.encrypt))
    self.df = df
    
def _request_search_terms():
    search_term = input(
        '\nspecify search term(s):\n'
        ' 1) index\t 3) username\n'
        ' 2) source\t 4) password\n$ '
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
    confirm = input(
        'are you sure? This can not be undone. [y/n]\n$ '
    )
    if confirm == 'y':
        if "table" in args:
            self.db._drop_table()
            self.db.init_db()
            self.df = self.db.get().applymap(self.rosetta.decrypt)
            
        elif "key" in args:
            new_key = kwargs.get('-k') or kwargs.get('--key') or getpass('new key:\n$ ')
            new_table = hashlib.pbkdf2_hmac(
                hash_name='sha512', 
                password=str.encode(new_key), 
                salt=str.encode(self.settings.table_salt),
                iterations=100000
            ).hex()
            self.rosetta = Rosetta(new_key, self.db.salt)
            self.db._drop_table()
            self.db._table = new_table
            self.db.init_db()
            self.db.update_db(self.df.applymap(self.rosetta.encrypt))
            self.df = self.db.get().applymap(self.rosetta.decrypt)
            
        elif "db" in args:
            print('\ndeleting all data from .db\n')
            self.db._reset_db()
            return False
        elif "app" in args:
            print('\ndeleting all internal .db files and removing config.\n')
            shutil.rmtree(os.path.join(HERE, 'db'))
            os.unlink(self.settings.name)
            return False
        else:
            print('no reset parameter specified.')
    else:
        print('aborting...')
    return True

def _settings(*args, **kwargs):
    db = DataBase()
    print_format = kwargs.get("-fmt") or kwargs.get("--format")
    if print_format in PRINT_FORMAT_SETTINGS:
        db.settings.update({"print_format": print_format})
    db.settings._write()
    

def _try_again(self):
    print('\naction not understood. Please try again, or type `exit` or `q` to quit\n')
    self._main()


class Session:
    def __init__(self, key):
        self.settings = Settings()
        self.db = DataBase(
            settings=self.settings,
            table=hashlib.pbkdf2_hmac(
                hash_name='sha512', 
                password=str.encode(key), 
                salt=str.encode(self.settings.table_salt),
                iterations=100000
            ).hex()
        ).init_db()
        self.rosetta = Rosetta(key, self.db.salt)
        self.df = self.db.get().applymap(self.rosetta.decrypt)

    def _main(self):
        action = input(
            '\nspecify action:\n'
            ' 1) get   3) make   5) remove   7) exit\n'
            ' 2) add   4) edit   6) settings\n$ '
        )

        if action in ('get', '1'):
            _get_from_db(self)
            self._main()
        elif action in ('add', '2'):
            _add_to_db(self)
            self._main()
        elif action in ('make', '3'):
            _make_db_entry(self)
            self._main()
        elif action in ('edit', '4'):
            _edit_db(self)
            self._main()
        elif action in ("remove", '5'):
            _remove_from_db(self)
            self._main()
        elif action in ('settings', '6'):
            self._settings_menu
        elif action in ('exit', 'q', '7'):
            print('bye!\n')
        elif action == 'ipython':
            _open_ipython(self)
            self._main()
        else:
            _try_again(self)

    @property
    def _settings_menu(self):
        settings_action = input(
            '\nselect option:\n'
            ' 1) reset key    4) list db path   7) dump db\n'
            ' 2) reset table  5) list archives  8) export db\n'
            ' 3) link db      6) consume csv    9) archive db\n'
            '$ '
        )
        if settings_action in ('1', 'reset key'):
            new_key = getpass('new key:\n$ ')
            _reset(self, 'key', **{'--key': new_key})
            self._main()
        elif settings_action in ('2', 'reset table'):
            _reset(self, 'table')
            self._main()
        elif settings_action in ('3', 'link db'):
            _link_db()
            print("restarting...")
            Session._interactive()
        elif settings_action in ('4', 'list db path'):
            _list_db('name')
            self._main()
        elif settings_action in ('5', 'list archives'):
            _list_db('archives')
            self._main()
        elif settings_action in ('6', 'consume csv'):
            _consume_csv(self)
            self._main()
        elif settings_action in ('7', 'dump db'):
            _dump_to_csv(self)
            self._main()
        elif settings_action in ('8', 'export db'):
            _export_db()
            self._main()
        elif settings_action in ('9', 'archive db'):
            _archive()
            print("restarting...")
            Session._interactive()


        elif settings_action == "RESET_DB":
            if _reset(self, "db"):
                self._main()
            else:
                print("TERMINATING")
        elif settings_action == "RESET_APP":
            if _reset(self, "app"):
                self._main()
            else:
                print("TERMINATING")
        elif settings_action in ("q", "exit"):
            print('bye!\n')
        else:
            _try_again(self)

    @staticmethod
    def _interactive():
        key = getpass('Please enter your vlt key:\n$ ')
        self = Session(key)
        self._main()

    @staticmethod
    def _static(cmd, args, kwargs):

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

        elif cmd in ('-c', 'comsume'):
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
