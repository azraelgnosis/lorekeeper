import click
import os
import sqlite3
from flask import current_app, g
from flask.cli import with_appcontext


class Row(sqlite3.Row):
    def __init__(self, cursor, values):
        self.cursor = cursor
        self.values = values
        self.columns = [col[0] for col in cursor.description]
        self.id = " ".join([str(val) for col, val in zip(self.columns, self.values) if 'id' in col]) # combines values with 'id' in column name.
        self.val = " ".join([str(val) for col, val in zip(self.columns, self.values) if 'val' in col]) # combines values with 'val' in column name.
        
        for col, val in zip(self.columns, self.values):
            setattr(self, col, val)

    def get(self, attr:str):
        """
        Returns the value of `attr` if present
            else, returns None.
        """
        return getattr(self, attr, None)

    def items(self) -> zip:
        return zip(self.columns, self.values)

    def to_dict(self):
        return dict(zip(self.columns, self.values))

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
            except TypeError: pass
            except ValueError: pass
        
        return val

    def __getitem__(self, key:str):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError

    def __repr__(self): return f"{self.id} {self.val}"


class LoreKeeper:
    #? maybe a dict of databases?
    def __init__(self, db_path:str):
        self._db_path = db_path
        self._db = None

    @property
    def db_path(self):
        return self._db_path

    @db_path.setter
    def db_path(self, path:str) -> None:
        if os.path.exists(path):
            self._db_path = path
        else:
            raise FileNotFoundError

    @property
    def db(self) -> sqlite3.Connection:
        if 'db' not in g:
            g.db = sqlite3.connect(
                current_app.config[self.db_path],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = Row

        return g.db

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

    def run_query(self, query:str, datatype=None) -> list:
        """
        If a SELECT statement, runs the query and
            if `datatype` converts the results to the datatype provided
            else returns a list of Row objects
        else, runs the query and commits to database.
        """

        results = None
        directive = query.split()[0]

        if directive.upper() == 'SELECT':
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
        comparators = ('=', '!=', '>', '>=', '<', '<=', 'IS', 'IS NOT', 'IN')
        conjunctions = ('AND', 'OR', 'NOT')

        WHERE = ""
        if isinstance(conditions, (int, str)):
            try:
                # assumes must be an id: "42" -> "table_id = 42"
                WHERE = f"{table}_id = {int(conditions)}"  
            except ValueError:
                if cls._contains(conditions, comparators):
                    WHERE = conditions
                else:
                    # or maybe a val: "Picard" -> "table_val = 'Picard'"
                    WHERE = f"{table}_val = '{conditions}'"  
            except TypeError:
                print("Somethin's up!")
                raise TypeError

        elif isinstance(conditions, dict):
            temp = []
            for key, val in conditions.items():
                if key in conjunctions:
                    temp.append(cls._where(table, val, conjunction=key))
                elif isinstance(key, tuple):
                    temp.append(f"{key[0]} {val} {coerce_type(key[1])}")
                else:
                    temp.append(f"{key} = {coerce_type(val)}")

            WHERE = f" {conjunction} ".join(temp)

        elif cls.is_iter(conditions):
            if any(cls.is_iter(condition) for condition in conditions):
                temp = []
                for condition in conditions:
                    temp.append(cls._where(table, condition))
                WHERE = f" {conjunction} ".join(temp)
            else:
                if len(conditions) == 1:
                    WHERE = cls._where(table, conditions[0])
                elif len(conditions) == 2:
                    WHERE = f"{conditions[0]} = {coerce_type(conditions[1])}"
                elif len(conditions) == 3:
                    WHERE = f"{conditions[0]} {conditions[1]} {coerce_type(conditions[2])}"

        return WHERE

    def select(self, table:str, columns='*', join=None, where=None, datatype=None) -> list:
        """
        SELECT `columns` FROM `table`
        """

        SELECT = "SELECT {COLUMNS} FROM {TABLE} {JOIN} {WHERE}" \
            .format(
                COLUMNS=self._columns(columns),
                TABLE=table,
                JOIN=self._join(table, join),
                WHERE=f"WHERE {self._where(where)}" if where else ""
            )

        results = self.get_db().execute(SELECT).fetchall()
        if datatype:
            results = [datatype.from_row(result) for result in results]

        return results

     #TODO: columns parameter 
    #? and maybe intersection of table columns and values
    def insert(self, table:str, values:dict, datatype=None) -> None:
        """
        INSERT INTO `table` VALUES (`values`)
        """
        
        if datatype:
            new_obj = datatype.from_dict(values)
            values = new_obj.to_dict()

        cols = self.get_columns(table)[1:]
        INSERT = "INSERT INTO `{TABLE}` ({COLUMNS}) VALUES ({VALUES})".format(
            TABLE=table,
            COLUMNS=", ".join(cols),
            VALUES=", ".join("?" * len(cols))
        )

        db = self.get_db()
        db.execute(
            INSERT,
            [f"{values.get(key)}" for key in cols]
        )
        db.commit()

    @staticmethod
    def coerce_type(obj):
        if isinstance(obj, str):
            try:
                if '.' in obj:
                    obj = float(obj)
                else:
                    obj = int(obj)
            except ValueError:
                obj = f"'{obj}'"
        
        return obj

    @staticmethod
    def is_iter(obj) -> bool:
        return hasattr(obj, '__iter__') and not isinstance(obj, str)

    @staticmethod
    def _contains(containing, contained) -> bool:
        return any(True for elem in contained if elem in containing)

    @classmethod
    def _init_db(cls) -> None:
        db = cls.get_db()

        with current_app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))

    @classmethod
    def _init_app(cls, app:Flask) -> None:
        app.teardown_appcontext(cls._close_db)
        app.cli.add_command(cls._init_db_command)

    @staticmethod
    def _close_db(e=None) -> None:
        db = g.pop('db', None)

        if db is not None:
            db.close()

    @classmethod
    @click.command('init-db')
    @with_appcontext
    def _init_db_command(cls) -> None:
        """Clear the existing data and create new tables."""

        cls._init_db()
        click.echo(f"Initialized the database.")
