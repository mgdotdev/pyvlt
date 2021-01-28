from getpass import getpass
import hashlib
import os
from pprint import pprint
import shutil

from IPython import embed as open_ipython

from .cmd_reader import reader
from .encryption import Rosetta
from .storage import DataBase

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMN_HEADERS = ['source', 'username', 'password']

def main():
    cmd, args, kwargs = reader()
    if cmd in {'-i', '--interactive'}:
        Session._interactive()
    elif cmd in {'-h', '--help'}:
        help_menu()
    else:
        Session._static(cmd, args, kwargs)

def help_menu():
    with open(os.path.join(HERE, 'help_text.txt'), 'r') as f:
        print(f.read())

def try_again(self):
    print('\naction not understood. Please try again, or type `exit` or `q` to quit\n')
    self._main()

def _get_from_db(self, *args, **kwargs):
    df = self.db.get()
    if "raw" in args:
        print('\n', df, '\n')
        return
    df = df.applymap(self.rosetta.decrypt)
    if "all" in args:
        print('\n', df, '\n')
        return
    source = kwargs.get('-s') or kwargs.get('--source')
    username = kwargs.get('-u') or kwargs.get('--username')
    password = kwargs.get('-p') or kwargs.get('--password')
    if all(x==None for x in (source, username, password)):
        raise ValueError(
            "<get> requires a source, username, and/or password to search against."
        )
    if source:
        df = df.loc[df['source'] == source]
    if username:
        df = df.loc[df['username'] == username]
    if password:
        df = df.loc[df['password'] == password]
    print('\n', df, '\n')

def _add_to_db(self, *args, **kwargs):
    source = kwargs.get('-s') or kwargs.get('--source') or input('\nspecify source:\n$ ')
    username = kwargs.get('-u') or kwargs.get('--username') or input('\nspecify username:\n$ ')
    password = kwargs.get('-p') or kwargs.get('--password') or input('\nspecify password:\n$ ')
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
    source = kwargs.get('-s') or kwargs.get('--source')
    username = kwargs.get('-u') or kwargs.get('--username')
    password = kwargs.get('-p') or kwargs.get('--password')
    if all(x==None for x in (source, username, password)):
        source = input('\nspecify source:\n$ ')
        username = input('\nspecify username:\n$ ')
        password = input('\nspecify password:\n$ ')
    if all(x=='' for x in (source, username, password)):
        raise ValueError(
            "<remove> requires a source, username, and/or password to proceed.\n"
            "if trying to reset table, see <reset table> in options or "
            "<vlt reset table> from shell."
        )
    df = self.df[
        (self.df['source'] != source) 
        & (self.df['username'] != username) 
        & (self.df['password'] != password)
    ]
    self.db.update_db(df.applymap(self.rosetta.encrypt))
    print('done.')
    return df

def _link_db(*args, **kwargs):
    path = kwargs.get('-f') or kwargs.get('--file') or kwargs.get("-a") or kwargs.get("--archive") or input(
        '\nplease enter a filepath to the external vlt db, or an archive index value:\n$ '
    )
    db = DataBase()
    if path in db.settings.settings["archives"].keys():
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
        for key, value in db.settings.archives.items():
            print("{:>5}: {}".format(int(key), value))
    elif "name" in args:
        print("    -  " + db.settings.name)
    else:
        pprint(db.settings.settings)

def _reset(self, *args, **kwargs):
    if "table" in args:
        self.db._drop_table()
        self.db.init_db()
        self.df = self.db.get().applymap(self.rosetta.decrypt)
    elif "key" in args:
        import pdb; pdb.set_trace()
        new_key = kwargs.get('-k') or kwargs.get('--key') or getpass('new key:\n$ ')
        new_table = hashlib.sha512(str.encode(new_key)).hexdigest()
        self.rosetta = Rosetta(new_key, self.db.salt)
        self.db._drop_table()
        self.db._table = new_table
        self.db.init_db()
        self.db.update_db(self.df.applymap(self.rosetta.encrypt))
        print('done.')

def _archive(*args, **kwargs):
    filename = kwargs.get('-n') or kwargs.get('--name') or input('\nplease enter a file name:\n$ ')
    if not filename.endswith('.db'):
        filename += '.db'
    db = DataBase()
    archive_file = os.path.join(os.path.dirname(db.settings.name), filename)
    os.rename(db.settings.name, archive_file)
    db.settings.archive(archive_file)
    db.settings._write()
    print('\ndone. restarting...')

class Session:
    def __init__(self, key):
        self.db = DataBase(
            table=hashlib.sha512(str.encode(key)).hexdigest()
        ).init_db()
        self.rosetta = Rosetta(key, self.db.salt)
        self.df = self.db.get().applymap(self.rosetta.decrypt)
        
    def _main(self):
        action = input(
            '\nspecify action:\n'
            ' 1) get \t 4) exit \n'
            ' 2) add \t 5) options \n'
            ' 3) remove\n$ '
        )
        if action in ('get', '1'):
            search_term = input(
                '\nspecify search term:\n'
                ' 1) source \t 3) password \n'
                ' 2) username \n$ '
            )
            try:
                index = int(search_term)
                search_term = COLUMN_HEADERS[index - 1]
            except ValueError:
                pass
            if search_term == "":
                print('\n', self.df) 
            elif search_term not in COLUMN_HEADERS:
                print(f'\nsearch term must be of type: {COLUMN_HEADERS}')     
            else:
                search_item = input('\nspecify search item:\n<str>\n$ ')
                if search_item:
                    print('\n', self.df.loc[self.df[search_term] == search_item])
                else:
                    print('\n', self.df)
            self._main()
        elif action in ('add', '2'):
            self.df = _add_to_db(self)
            self._main()
        elif action in ("remove", '3'):
            self.df = _remove_from_db(self)
            self._main()
        elif action in ('exit', 'q', '4'):
            action = None
            print('bye!\n')
        elif action in ('options', '5'):
            self._options_menu
        elif action == 'ipython':
            open_ipython()
            self._main()
        else:
            try_again(self)

    @property
    def _options_menu(self):
        options_action = input(
            '\nselect option:\n'
            ' 1) change key \t 3) db settings\n'
            ' 2) reset table  4) open IPython terminal\n$ '
        )
        if options_action in ('1', 'change key'):
            new_key = getpass('new key:\n$ ')
            confirm = input('are you sure? this action can not be undone. [y/n]\n$ ')
            if confirm == 'y':
                _reset(self, 'key', **{'--key': new_key})
            else:
                print('aborting...')
            self._main()
        elif options_action in ('2', 'reset table'):
            confirm = input('are you sure? This can not be undone. [y/n]\n$ ')
            if confirm == 'y':
                _reset(self, 'table')
                print('done.')
            else:
                print('aborting...')
            self._main()
        elif options_action in ('3', 'db settings'):
            self._db_settings_menu
        elif options_action in ('4', 'ipython', 'open ipython terminal'):
            print('\n')
            open_ipython()
            self._main()
        elif options_action == "RESET_ALL":
            confirm = input('are you sure? This can not be undone. [y/n]\n$ ')
            if confirm == 'y':
                print('\nINITIATING SELF DESTRUCT\n')
                self.db._reset_db()
                print('done.')
            else:
                print('aborting...')
                self._main()
        else:
            try_again(self)

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
            Session._interactive()

        elif db_settings_action in ('2', 'export db'):
            _export_db()
            self._main()

        elif db_settings_action in ('3', 'archive db'):
            _archive()
            Session._interactive()

        elif db_settings_action in ('4', 'list archives'):
            _list_db('archives')
            self._main()

        elif db_settings_action in ('5', 'list path'):
            _list_db('name')
            self._main()
        
        else:
            try_again(self)

    @staticmethod
    def _interactive():
        key = getpass('Please enter your session key:\n$ ')
        self = Session(key)
        self._main()

    @staticmethod
    def _static(cmd, args, kwargs):

        if cmd in ('-l', 'lnk', 'link'):
            return _link_db(*args, **kwargs)

        if cmd in ('-e', 'exp', 'export'):
            return _export_db(*args, **kwargs)

        if cmd in ('-ls', 'ls', 'list'):
            return _list_db(*args, **kwargs)

        if cmd in ('-ar', 'archive'):
            return _archive(*args, **kwargs)

        key = kwargs.get('-k') or kwargs.get("--key")
        if not key:
            key = getpass('Please enter your session key:\n$ ')
        self = Session(key)

        if cmd in ('-g', 'get'):
            return _get_from_db(self, *args, **kwargs)

        elif cmd in ('+', '-a', 'add'):
            return _add_to_db(self, *args, **kwargs)

        elif cmd in ('-', '-rm', 'rm', 'remove'):
            return _remove_from_db(self, *args, **kwargs)

        elif cmd in ('-rs', 'reset'):
            return _reset(self, *args, **kwargs)

        elif cmd == 'ipython':
            print('\nvlt objects are callable through `self`.\n')
            open_ipython()
