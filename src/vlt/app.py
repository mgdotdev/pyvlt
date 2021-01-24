from getpass import getpass
import os.path

from vlt.cmd_reader import reader
from vlt.encryption import Rosetta
from vlt.storage import DataBase

HERE = os.path.dirname(os.path.abspath(__file__))
COLUMN_HEADERS = ['source', 'username', 'password']

def main():
    cmd, args, kwargs = reader()

    if cmd == '-i':
        Session.interactive()
    elif cmd == '-s':
        Session.static(cmd, args, kwargs)
    elif cmd in {'-h', '--help'}:
        help_menu()

def help_menu():
    with open(os.path.join(HERE, 'help_text.txt'), 'r') as f:
        print(f.read())

def try_again(self):
    print('\naction not understood. Please try again, or type `exit` or `q` to quit\n')
    self.main()

class Session:
    def __init__(self, password):
        self.rosetta = Rosetta(password)
        import pdb; pdb.set_trace()
        self.db = DataBase().create_db()

    def main(self):
        action = input('specify action:\n| 1) get | 2) add | 3) exit | 4) options |\n$ ')
        if action in ('get', '1'):
            search_term = input('specify search term:\n| 1) source | 2) username | 3) password |\n$ ')
            try:
                index = int(search_term)
                search_term = COLUMN_HEADERS[index - 1]
            except ValueError:
                pass
            if search_term not in COLUMN_HEADERS:
                print(f'search term must be of type: {COLUMN_HEADERS}')
                self.main()
            search_item = input('specify search item:\n<str>\n$ ')
            
            if search_item:
                print('\n', self.df.loc[self.df[search_term] == search_item], '\n')
            else:
                print('\n', self.df, '\n')
            self.main()

        elif action in ('add', '2'):
            source = self.rosetta.encrypt(input('specify source:\n$ '))
            username = self.rosetta.encrypt(input('specify username:\n$ '))
            password = self.rosetta.encrypt(input('specify password:\n$ '))
            self.db.add(source, username, password)
            self.df = self.db.get().applymap(self.rosetta.decrypt)
            print('done.\n')
            self.main()

        elif action in ('exit', 'q', '3'):
            print('bye!\n')

        elif action in ('options', '4'):
            self.options_menu

        else:
            try_again(self)

    @property
    def options_menu(self):
        options_action = input('select option:\n| 1) change token | 2) reset database |\n$ ')
        if options_action in ('1', 'change token'):
            new_token = getpass('new token:\n$ ')
            confirm = input('are you sure? this action can not be undone. y/n\n$ ')
            if confirm == 'y':
                self.rosetta = Rosetta(new_token)
                self.db._reset_db()
                for i in self.df.index:
                    source = self.rosetta.encrypt(self.df.loc[i,'source'])
                    username = self.rosetta.encrypt(self.df.loc[i, 'username'])
                    password = self.rosetta.encrypt(self.df.loc[i, 'password'])
                    self.db.add(source, username, password)
                print('done.\n')
                self.main()
            else:
                print('aborting...\n')
                self.main()
        elif options_action in ('2', 'reset database'):
            confirm = input('are you sure? this action can not be undone. y/n\n$ ')
            if confirm == 'y':
                self.db._reset_db()
                print('done.\n')
                self.main()
            else:
                print('aborting...\n')
                self.main()                    
        else:
            try_again(self)

    @staticmethod
    def interactive():
        pwd = getpass('Please enter your session key:\n$ ')
        self = Session(pwd)
        self.df = self.db.get().applymap(self.rosetta.decrypt)
        self.main()

    @staticmethod
    def static(cmd, args, kwargs):
        raise RuntimeError('this feature is not yet implemented')

        key = kwargs.get('-k')
        if not key:
            raise ValueError('encryption key must be passed as -k <VALUE>')
        self = Session(key)

        