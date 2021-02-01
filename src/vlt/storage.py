import hashlib
import os
import random
import sqlite3

import pandas as pd

from .settings import Settings

HERE = os.path.dirname(os.path.abspath(__file__))

def make_salt():
    return "".join([chr(random.randint(0,255)) for _ in range(64)])

class DataBaseManager:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.sql = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.sql.close()
        self.conn.close()

    def execute(self, *args, r=True):
        res = self.sql.execute(*args)
        if r is True: 
            return self
        else: 
            return res

    def executemany(self, *args, r=True):
        res = self.sql.executemany(*args)
        if r is True:
            return self
        else:
            return res


    def commit(self):
        self.conn.commit()

class DataBase:
    def __init__(self, name=None, settings=None, key=None):
        self._name = (name or "vlt.db")
        self.settings = (settings or Settings())
        self._table = hashlib.pbkdf2_hmac(
            hash_name='sha512', 
            password=str.encode(key), 
            salt=str.encode(self.table_salt),
            iterations=100000
        ).hex()
        self.init_db()
        
    @property
    def name(self):
        name = self.settings["name"]
        if not name:
            self.settings.update(
                {"name": os.path.join(HERE, 'db', self._name)}
            )
            self.settings._write()
            name = self.settings["name"]
        if not os.path.isdir(os.path.dirname(name)):
            os.makedirs(os.path.dirname(name))
        return name

    @property
    def table(self):
        return "table_" + self._table

    @property
    def table_salt(self):
        if not self.check_table_exists("salts"):
            self.init_salts()
        return self.get_salt("table_salt")

    def init_salts(self):
        self.execute(
            f"""
            CREATE TABLE IF NOT EXISTS salts (
                id BLOB,
                salt BLOB
            )
            """,
            commit=False
        )

        self.add_salt(
            "table_salt", 
            make_salt()
        )

    def get_salt(self, _id):
        with DataBaseManager(self.name) as sql:
            salt = [item[0] for item in sql.execute(
                f"SELECT salt FROM salts WHERE id = '{_id}';",
                r=False
            )]
        if salt:
            return salt[0]
        salt = make_salt()
        self.add_salt(self.table, salt)            
        return salt

    def add_salt(self, _id, table_salt):
        self.execute(
            f"""
            INSERT INTO salts (
                id, salt
            ) VALUES (?, ?)
            """, (_id, table_salt)
        )       

    def execute(self, *args, commit=True):
        with DataBaseManager(self.name) as sql:
            exe = sql.execute(*args)
            if commit:
                exe.commit()

    def executemany(self, *args, commit=True):
        with DataBaseManager(self.name) as sql:
            exe = sql.executemany(*args)
            if commit:
                exe.commit()

    def check_table_exists(self, name):
        if name in self._table_names:
            return True
        return False

    def init_db(self):
        if not self.check_table_exists("salts"):
            self.init_salts()

        self.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                id INTEGER PRIMARY KEY,
                source BLOB,
                username BLOB,
                password BLOB
            )
            """
        )
        return self

    def add(self, source, username, password):
        self.execute(
            f"""
            INSERT OR IGNORE INTO {self.table} (
                source, username, password
            ) VALUES (?, ?, ?)
            """, (source, username, password)
        )

    def update_db(self, df):
        self.execute(
            f"""
            DELETE FROM {self.table};
            """
        )
        self.add_list_of_lists(df.values.tolist())

    def add_list_of_lists(self, list_of_lists):
        self.executemany(
            f"""
            INSERT OR IGNORE INTO {self.table} (
                source, username, password
            ) VALUES (?, ?, ?)
            """, list_of_lists
        )        

    def get(self, table=None):
        with DataBaseManager(self.name) as sql:
            if table:
                return pd.read_sql_query(f"SELECT * FROM {table}", sql.conn)
            return pd.read_sql_query(
                f"SELECT source, username, password FROM {self.table}",
                sql.conn
            )

    @property        
    def _table_names(self):
        with DataBaseManager(self.name) as sql:
            names = [item[0] for item in sql.execute(
                "SELECT name FROM sqlite_master WHERE type='table'",
                r=False
            )]
        return names

    def _drop_table(self, name=None):
        self.execute(
            f"""
            DROP TABLE {name if name else self.table}
            """
        )
        
    def _reset_db(self):
        for name in self._table_names:
            self._drop_table(name)
        self.init_db()
