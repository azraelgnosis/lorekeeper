from abc import ABCMeta
import click
import os
import sqlite3
from flask import current_app, Flask, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from .consts import *
from .models import Row, Table

class LoreKeeper(metaclass=ABCMeta):
    #? maybe a dict of databases?
    def __init__(self, db_name:str=None):
        self.db_name = db_name
        self._db = None
        self._table_map = {}

    def __repr__(self): return self.__class__

    @property
    def tables(self) -> list:
        if not self._tables:
            self._tables = self.select("sqlite_master", columns=["name"], where={"type": "table"}, datatype=Table)
            # def get_tables(self) -> list:
        self.select(table='sqlite_master')

        tables = self.db.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        tables = [Table(table['name'], db) for table in tables[1:]]

        return tables

    @property  # TODO: does this need to be a property?
    def table_map(self) -> dict:
        return self._table_map

    @property
    def db(self) -> sqlite3.Connection:
        if 'db' not in g:
            g.db = sqlite3.connect(
                current_app.config[self.db_name],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = Row

        return g.db

    def fetch_all(self, query) -> list:  # TODO huh?
        """
        """

        results = self.db.execute(query).fetchall()

        return results

    def run_query(self, query:str, datatype=None) -> list:
        """
        If a SELECT statement, runs the query and
            if `datatype` converts the results to the datatype provided
            else returns a list of Row objects
        else, runs the query and commits to database.
        """

        results = None
        directive = query.split()[0]

        if directive.upper() == SELECT:
            results = self.db.execute(query).fetchall()

            if datatype:
                results = [datatype.from_row(result) for result in results]
        
        else:
            self.db.execute(query)
            self.db.commit()

        return results

    #TODO: somehow connect joining on the same table multiples times to the select columns
    @classmethod
    def _join(cls, from_table:str, join:dict) -> str:
        """
        Creates a left join clause for each table-column pair in `join`.
        """

        JOIN = ""
        if join:
            joins = []
            if isinstance(join, dict):
                for idx, (table, on) in enumerate(join.items()):
                    joins.append(f"LEFT JOIN {table} AS {table}{idx} ON {table}{idx}.{on} = {from_table}.{on}")
            elif cls._is_iter(join):
                for idx, table in enumerate(join):
                    joins.append(f"LEFT JOIN {table} AS {table}{idx} ON {table}{idx}.{table}_id = {from_table}.{table}_id")
                raise NotImplementedError("Table names are plural; default id columns are singular.") #TODO

            JOIN = "\t\n".join(joins)

        return JOIN

    def _get_columns(self, table:str) -> list:
        """
        Retrieves a list of `table` columns.

        :param table: Name of database table.
        :return: List of columns.
        """

        cursor = self.db.execute(f"SELECT * FROM {table} LIMIT 0")
        columns = [col[0] for col in cursor.description]

        return columns

    @classmethod
    def _columns(cls, columns) -> str:
        """
        If `columns` is a 
            str: returns unaltered.
            dict: joins table-column pairs as '`table`.column'.
            iterable: joins columns.
        """

        COLUMNS = ""
        if isinstance(columns, str):
            COLUMNS += columns
        elif isinstance(columns, dict):
            COLUMNS += ", ".join(f"`{table}`.{column}" for table, column in columns.items())
        elif cls._is_iter(columns):
            COLUMNS += ", ".join(columns)

        return COLUMNS

    @classmethod
    def _where(cls, table:str, conditions, conjunction='AND'):
        """
        
        """

        comparators = ('=', '!=', '>', '>=', '<', '<=', ' IS ', ' IS NOT ', ' IN ')
        conjunctions = (' AND ', ' OR ', ' NOT ')

        WHERE = ""
        if isinstance(conditions, (int, str)):
            try:
                # assumes `conditions` must be an id: "42" -> "table_id = 42"
                WHERE = f"`{table}`.{table}_id = {int(conditions)}"  
            except ValueError:
                if cls._contains(conditions, comparators):
                    WHERE = conditions
                else:
                    # or maybe a val: "Picard" -> "table_val = 'Picard'"
                    WHERE = f"`{table}`.{table}_val = '{conditions}'"  
            except TypeError:
                print("Somethin's up!")
                raise TypeError

        elif isinstance(conditions, dict):
            temp = []
            for key, val in conditions.items():
                if key in conjunctions:
                    temp.append(cls._where(table, val, conjunction=key))
                elif isinstance(key, tuple):
                    temp.append(f"{key[0]} {val} {cls._coerce_type(key[1])}")
                else:
                    temp.append(f"{key} = {cls._coerce_type(val)}")

            WHERE = f" {conjunction} ".join(temp)

        elif cls._is_iter(conditions):
            if any(cls._is_iter(condition) for condition in conditions):
                temp = []
                for condition in conditions:
                    temp.append(cls._where(table, condition))
                WHERE = f" {conjunction} ".join(temp)
            else:
                if len(conditions) == 1:
                    WHERE = cls._where(table, conditions[0])
                elif len(conditions) == 2:
                    WHERE = f"{conditions[0]} = {cls._coerce_type(conditions[1])}"
                elif len(conditions) == 3:
                    WHERE = f"{conditions[0]} {conditions[1]} {cls._coerce_type(conditions[2])}"

        return WHERE

    def select(self, table:str, columns='*', join=None, where=None, datatype=None) -> list:
        """SELECT `columns` FROM `table` [LEFT JOIN `join`] [WHERE `where`]"""

        SELECT = "SELECT {COLUMNS} FROM {TABLE} {JOIN} {WHERE}" \
            .format(
                COLUMNS=self._columns(columns),
                TABLE=table,
                JOIN=self._join(table, join),
                WHERE=f"WHERE {self._where(table, where)}" if where else ""
            )

        results = self.db.execute(SELECT).fetchall()
        if datatype:
            datatype = self.table_map.get(table, datatype)
            results = [datatype.from_row(result) for result in results]

        return results

     #TODO: columns parameter 
    
    #? will probaly need to add validation
    def select_one(self, table:str, where, columns:list='*', datatype=None):
        return self.select(table, columns, where, datatype)[0]

    #? and maybe intersection of table columns and values
    def insert(self, table:str, values:dict, datatype=None) -> None:
        """
        INSERT INTO `table` VALUES (`values`)
        """
        
        if datatype:
            new_obj = datatype.from_dict(values)
            values = new_obj.to_dict()

        cols = self._get_columns(table)[1:]  # TODO: intersection of table columns and values keys
        INSERT = "INSERT INTO `{TABLE}` ({COLUMNS}) VALUES ({VALUES})".format(
            TABLE=table,
            COLUMNS=", ".join(cols),
            VALUES=", ".join("?" * len(cols))
        )
        
        if isinstance(values, dict):
            values = list(map(values.get, cols))  # [f"{values.get(key)}" for key in cols]

        self.db.execute(INSERT, values)
        self.db.commit()

    def update(self, table:str, values:dict, where:dict) -> None:
        """
        UPDATE `table`
            SET `values`
            WHERE `where`
        """

        query = "UPDATE `{TABLE}` SET {SET} WHERE {WHERE}".format(
            TABLE=table,
            SET=", ".join([f"{column}=?" for column in values.keys()]),
            WHERE = self._where(table, where)
        )
        self.db.execute(query, list(values.values()))
        self.db.commit()

    def delete(self, table:str, where:dict) -> None:
        """
        DELETE FROM `table` WHERE `where`;
        """

        query = "DELETE FROM {TABLE} WHERE {WHERE};".format(
            TABLE=table,
            WHERE=_where(where)
        )
        self.db.execute(query)
        self.db.commit()

# ==========================================================================================

    #! check tables property above
    def get_table(table_name:str) -> Table: raise NotImplementedError
    def get_table(self, name:str) -> Table:
        """
        Selects everything from `table`.

        Returns Table object.
        """

        table = Table(name, self.db)
        table.rows = select(name)

        return table

# ==========================================================================================
        
    @classmethod
    def _coerce_type(cls, val, separator=",", none=None):
        """
        Coerces `val` as a float or int if applicable,
        if `val` is None, returns the value of `none`
        else returns original value.

        :param val: Value to coerce.
        """

        if val is None:
            val = none
        elif isinstance(val, str):
            if len(coll := val.split(separator)) > 1:
                val = [cls._coerce_type(elem.strip()) for elem in coll]

            try:
                if "." in str(val):
                    val = float(val)
                else:
                    val = int(val)
            except (TypeError, ValueError):
                val = f"'{val}'"

        return val

    @staticmethod
    def _is_iter(obj) -> bool:
        return hasattr(obj, '__iter__') and not isinstance(obj, str)

    @staticmethod
    def _contains(containing, contained) -> bool:
        return any(True for elem in contained if elem in containing)

    def __repr__(self): return f"{self.__class__.__name__}: {self.db_name}"

# ==========================================================================================
    # database initialization methods

    @classmethod
    def init_app(cls, app:Flask) -> None:
        app.teardown_appcontext(cls._close_db)
        app.cli.add_command(cls._init_db_command)

    def _init_db(self) -> None:
        with current_app.open_resource('schema.sql') as f:
            self.db.executescript(f.read().decode('utf8'))
        self.update(Tables.USER, {PASSWORD: generate_password_hash('admin')}, where=1)

    @staticmethod
    def _close_db(e=None) -> None:
        db = g.pop('db', None)

        if db:
            db.close()

    @staticmethod
    @click.command('init-db')
    @click.argument('database')
    @with_appcontext
    def _init_db_command(database:str) -> None:
        """Clear the existing data and create new tables."""

        LoreKeeper(database)._init_db()
        click.echo(f"Initialized the database.")

    # TODO
    # @click.command('backup-db')
    # def backup_db() -> None:
    #     pass
