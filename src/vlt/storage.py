import os
import sqlite3

import pandas as pd

class DataBaseManager:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.sql = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.sql.close()
        self.conn.close()

    def execute(self, *args, r=False):
        res = self.sql.execute(*args)
        if r is False: 
            return self
        else: 
            return res

    def commit(self):
        self.conn.commit()

class DataBase:
    def __init__(self):
        self.name = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'database.db'
        )

    def execute_and_commit(self, *args):
        with DataBaseManager(self.name) as sql:
            sql.execute(*args).commit()

    def create_db(self):
        self.execute_and_commit(
            """
            CREATE TABLE IF NOT EXISTS storage (
                id INTEGER PRIMARY KEY,
                source BLOB,
                username BLOB,
                password BLOB
            )
            """
        )
        return self

    def add(self, source, username, password):
        self.execute_and_commit(
            f"""
            INSERT OR IGNORE INTO storage(
                source, username, password
            ) VALUES (?, ?, ?)
            """, [source, username, password]
        )

    def get(self):
        with DataBaseManager(self.name) as sql:
            df = pd.read_sql_query(
                f"""
                SELECT source, username, password FROM storage
                """,
                sql.conn
            )
        return df
        
    def _get_table_names(self):
        with DataBaseManager(self.name) as sql:
            names = [x[0] for x in sql.execute(
                "SELECT name FROM sqlite_master WHERE type='table'",
                r=True
            )]

        return names

    def _drop_table(self, name):
        self.execute_and_commit(
            f"""
            DROP TABLE {name}
            """
        )

    def _reset_db(self):
        names = self._get_table_names()
        for name in names:
            self._drop_table(name)
        self.create_db()
