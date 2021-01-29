from getpass import getpass
import hashlib
import json
import os
import random
import shutil

from IPython import embed as open_ipython
import pandas as pd

from .cmd_reader import reader
from .encryption import Rosetta
from .storage import DataBase

HERE = os.path.dirname(os.path.abspath(__file__))
PRINT_FORMAT_SETTINGS = ['df', 'v', 'h']

def main():
    cmd, args, kwargs = reader()
    if cmd in {'-i', '--interactive'}:
        Session._interactive()
    elif cmd in {'-h', '--help'}:
        _help_menu()
    else:
        Session._static(cmd, args, kwargs)

def _help_menu():
    with open(os.path.join(HERE, 'help_text.txt'), 'r') as f:
        print(f.read())

def _try_again(self):
    print('\naction not understood. Please try again, or type `exit` or `q` to quit\n')
    self._main()

def print_df(df, option=None):
    if not option or option == 'df':
        print('\n', df, '\n')
        return
    indexes = [str(x) for x in df.index.tolist()]
    df = df.values.tolist()
    if option == "v":        
        if len(df) == 0:
            print("\nThe query produced zero results.\n")
        else:
            for index, item in zip(indexes, df):
                print(
                    f"{index}.\n"
                    f"  SOURCE: {item[0]}\n"
                    f"USERNAME: {item[1]}\n"
                    f"PASSWORD: {item[2]}\n"
                )
    elif option == 'h':
        lengths = [
            max([len(i) for i in indexes] + [len('ID')]),
            max([len(x[0]) for x in df] + [len('SOURCE')]), 
            max([len(x[1]) for x in df] + [len('USERNAME')]),
            max([len(x[2]) for x in df] + [len('PASSWORD')])
        ]
        print("  ".join([
            f"ID{' ' * (lengths[0] - len('ID'))}",
            f"SOURCE{' ' * (lengths[1] - len('SOURCE'))}",
            f"USERNAME{' ' * (lengths[2] - len('USERNAME'))}",
            f"PASSWORD{' ' * (lengths[3] - len('PASSWORD'))}"
        ]))
        print("  ".join(["-" * l for l in lengths]))
        for index, x in zip(indexes, df):
            x = [index] + x
            print("  ".join([
                item + (" " * (length - len(item))) 
                for item, length in zip(x, lengths)
            ]))

def _request_search_terms():
    search_term = input(
        '\nspecify search term(s):\n'
        ' 1) source \t 3) password \n'
        ' 2) username \n$ '
    )
    args, kwargs = [], {}
    if search_term == "":
        args.append("all")

    elif search_term == "raw":
        args.append("raw")

    if any(c in search_term for c in ('1', 'source')):
        kwargs.update({'--source': input('\nspecify source:\n$ ')})

    if any(c in search_term for c in ('2', 'username')):
        kwargs.update({'--username': input('\nspecify username:\n$ ')})

    if any(c in search_term for c in ('3', 'password')):
        kwargs.update({'--password': input('\nspecify password:\n$ ')})
    return args, kwargs
            

def _get_from_db(self, *args, **kwargs):
    format_option = kwargs.get("-fmt") or kwargs.get("--format") or self.settings.print_format

    if args == () and kwargs == {}:
        args, kwargs = _request_search_terms()
    df = self.db.get()
    if "raw" in args:
        return print_df(df, format_option)

    df = df.applymap(self.rosetta.decrypt)
    if "all" in args:
        return print_df(df, format_option)

    source = kwargs.get('-s') or kwargs.get('--source')
    username = kwargs.get('-u') or kwargs.get('--username')
    password = kwargs.get('-p') or kwargs.get('--password')
    if all(x==None for x in (source, username, password)):
        raise ValueError(
            "<get> requires a source, username, and/or password to search against."
        )
    import pdb; pdb.set_trace()
    if source:
        df = df.loc[df['source'].str.contains(source)]
    if username:
        df = df.loc[df['username'] == username]
    if password:
        df = df.loc[df['password'] == password]
    print_df(df, format_option)

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
    print('done.')
    return df

def _remove_from_db(self, *args, **kwargs):
    index = kwargs.get('-i') or kwargs.get('--index')
    df = self.df[self.df.index != int(index)]
    self.db.update_db(df.applymap(self.rosetta.encrypt))
    print('done.')
    return df

def _edit_db(self, *args, **kwargs):
    index = kwargs.get('-i') or kwargs.get('--index')
    if not index:
        index = _get_index(self)
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
    print("done.")
    return df

def _link_db(*args, **kwargs):
    if len(args) > 0:
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
    if not db.settings.archives:
        pass
    elif path in db.settings.settings["archives"].keys():
        path = db.settings.settings["archives"][path]
    if not (os.path.isfile(path) and path.endswith('.db')):
        raise FileNotFoundError('argument passed should be of filetype .db')
    if db.settings.name:
        db.settings.archive(db.settings.name)
        db.settings.update({"name": path})
    else:    
        db.settings.update({"name": path})
    if not db.check_table_exists('settings'):
        raise LookupError("passed .db file doesn't have <settings> table")
    if not db.salt:
        raise LookupError("passed .db file doesn't have a <salt> encryption token")
    db.settings._write()
    print('done.')

def _export_db(*args, **kwargs):
    if args:
        path = args[0]
    else:
        path = kwargs.get('-p') or kwargs.get('--path') or input(
            '\nplease enter a directory path to copy the vlt db to:\n$ '
        )
    path = os.path.normpath(path)
    db = DataBase()
    if not os.path.isdir(path):
        check = input(
            'path passed is not a currently working directory. '
            'Would you like to create it? [y/n]\n$ '
        )
        if check == 'y':
            os.makedirs(path)
            shutil.copy2(db.settings.name, path)
        else:
            print('aborting...')
    else:
        shutil.copy2(db.settings.name, path)
        print('done.')

def _list_db(*args, **kwargs):
    db = DataBase()
    if "archives" in args:
        archives = db.settings.archives
        if type(archives) == dict:
            for key, value in archives.items():
                print("{:>5}: {}".format(int(key), value))
        else:
            print('None')
    elif "name" in args:
        print("    -  " + db.settings.name)
    else:
        print(json.dumps(db.settings.settings, indent=2, sort_keys=True))

def _reset(self, *args, **kwargs):
    if "table" in args:
        self.db._drop_table()
        self.db.init_db()
        self.df = self.db.get().applymap(self.rosetta.decrypt)
    elif "key" in args:
        new_key = kwargs.get('-k') or kwargs.get('--key') or getpass('new key:\n$ ')
        new_table = hashlib.sha512(str.encode(new_key)).hexdigest()
        self.rosetta = Rosetta(new_key, self.db.salt)
        self.db._drop_table()
        self.db._table = new_table
        self.db.init_db()
        self.db.update_db(self.df.applymap(self.rosetta.encrypt))
        print('done.')
    elif "all" in args:
        confirm = input(
            'are you sure? This can not be undone. [y/n]\n$ '
        )
        if confirm == 'y':
            print('\nINITIATING SELF DESTRUCT\n')
            self.db._reset_db()
            print('done.')
            return False
        else:
            print('aborting...')
    else:
        print('no reset parameter specified.')
    return True

def _archive(*args, **kwargs):
    filename = kwargs.get('-n') or kwargs.get('--name') or input('\nplease enter a file name:\n$ ')
    if not filename.endswith('.db'):
        filename += '.db'
    db = DataBase()
    archive_file = os.path.join(os.path.dirname(db.settings.name), filename)
    os.rename(db.settings.name, archive_file)
    db.settings.archive(archive_file)
    db.settings._write()
    print('done.')

def _settings(*args, **kwargs):
    db = DataBase()
    print_format = kwargs.get("-fmt") or kwargs.get("--format")
    if print_format in PRINT_FORMAT_SETTINGS:
        db.settings.update({"print_format": print_format})
    db.settings._write()
    print('done.')

def _get_index(self):
    index = input(
        "\npass the index value of the entry to be removed."
        "\nif unknown, press enter to search. \n$ "
    )
    if not index:
        _get_from_db(self)
        index = _get_index(self)
    return index

class Session:
    def __init__(self, key):
        self.db = DataBase(
            table=hashlib.sha512(str.encode(key)).hexdigest()
        ).init_db()
        self.rosetta = Rosetta(key, self.db.salt)
        self.settings = self.db.settings
        self.df = self.db.get().applymap(self.rosetta.decrypt)

    def _main(self):
        action = input(
            '\nspecify action:\n'
            ' 1) get \t 4) remove \n'
            ' 2) add \t 5) exit \n'
            ' 3) edit \t 6) settings \n$ '
        )
        if action in ('get', '1'):
            _get_from_db(self)
            self._main()
        elif action in ('add', '2'):
            self.df = _add_to_db(self)
            self._main()
        elif action in ('edit', '3'):
            index = _get_index(self)
            self.df = _edit_db(self, **{'--index': index})
            self._main()
        elif action in ("remove", '4'):
            index = _get_index(self)
            self.df = _remove_from_db(self, **{'--index': index})
            self._main()
        elif action in ('exit', 'q', '5'):
            print('bye!\n')
        elif action in ('settings', '6'):
            self._settings_menu
        elif action == 'ipython':
            open_ipython()
            self._main()
        else:
            _try_again(self)

    @property
    def _settings_menu(self):
        settings_action = input(
            '\nselect option:\n'
            ' 1) change key \t 3) db settings\n'
            ' 2) reset table  4) open IPython terminal\n$ '
        )
        if settings_action in ('1', 'change key'):
            new_key = getpass('new key:\n$ ')
            confirm = input(
                'are you sure? this action can not be undone. [y/n]\n$ '
            )
            if confirm == 'y':
                _reset(self, 'key', **{'--key': new_key})
            else:
                print('aborting...')
            self._main()
        elif settings_action in ('2', 'reset table'):
            confirm = input(
                'are you sure? This can not be undone. [y/n]\n$ '
            )
            if confirm == 'y':
                _reset(self, 'table')
                print('done.')
            else:
                print('aborting...')
            self._main()
        elif settings_action in ('3', 'db settings'):
            self._db_settings_menu
        elif settings_action in ('4', 'ipython', 'open ipython terminal'):
            print('\n')
            open_ipython()
            self._main()
        elif settings_action == "RESET_ALL":
            reset_all = _reset(self, "all")
            if not reset_all:
                self._main()
        else:
            _try_again(self)

    @property
    def _db_settings_menu(self):
        db_settings_action = input(
            '\nselect action:\n'
            ' 1) link external db \t 4) list archives\n'
            ' 2) export db \t\t 5) list db path\n'
            ' 3) archive db\n$ '
        )

        if db_settings_action in ('1', 'link external db'):
            _link_db()
            print("restarting...")
            Session._interactive()

        elif db_settings_action in ('2', 'export db'):
            _export_db()
            self._main()

        elif db_settings_action in ('3', 'archive db'):
            _archive()
            print("restarting...")
            Session._interactive()

        elif db_settings_action in ('4', 'list archives'):
            _list_db('archives')
            self._main()

        elif db_settings_action in ('5', 'list db path'):
            _list_db('name')
            self._main()
        
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

        if cmd in ('-s', 'settings'):
            return _settings(*args, **kwargs)

        key = kwargs.get('-k') or kwargs.get("--key")
        if not key:
            key = getpass('Please enter your vlt key:\n$ ')
        self = Session(key)

        if cmd in ('-g', 'get'):
            return _get_from_db(self, *args, **kwargs)

        elif cmd in ('+', '-a', 'add'):
            return _add_to_db(self, *args, **kwargs)

        elif cmd in ('-e', 'edit'):
            return _edit_db(self, *args, **kwargs)

        elif cmd in ('-', '-rm', 'rm', 'remove'):
            return _remove_from_db(self, *args, **kwargs)

        elif cmd in ('-rs', 'reset'):
            return _reset(self, *args, **kwargs)

        elif cmd == 'ipython':
            print('\nvlt objects are callable through `self`.\n')
            open_ipython()
