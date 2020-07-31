import sqlite3
from flask import current_app, g

class Row(sqlite3.Row):
    def __init__(self, cursor, values):
        self.cursor = cursor
        self.values = values
        self.columns = [col[0] for col in cursor.description]
        self.val = " ".join([val for col, val in zip(self.columns, self.values) if 'val' in col]) # combines values with 'val in column name.

        for col, val in zip(self.columns, self.values):
            setattr(self, col, val)

    def get(self, attr:str):
        """
        Returns the value of `attr` if present
            else, returns None.
        """

        attribute = None
        try:
            attribute = getattr(self, attr)
        except AttributeError: pass

        return attribute

    def items(self):
        return zip(self.columns, self.values)

    def __getitem__(self, key:str):
        try:
            return getattr(self, key)
        except AttributeError:
            raise ValueError

    def __repr__(self): return f"{self.val}"

class LoreKeeper:
    def __init__(self, db_path:str):
        self.db_path = db_path

    #? def set_db_path(self, path:str): pass

    def get_db(self) -> sqlite3.Connection:
        if 'db' not in g:
            g.db = sqlite3.connect(
                current_app.config[self.db_path],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = Row

        return g.db

    #TODO: somehow connect joining on the same table multiples times to the select columns
    @staticmethod
    def _join(from_table:str, join:dict) -> str:
        """
        Creates a left join clause for each table-column pair in `join`.
        """

        JOIN = ""
        if join:
            joins = []
            for idx, (table, on) in enumerate(join.items()):
                joins.append(f"LEFT JOIN {table} AS {table}{idx} ON {table}{idx}.{on} = {from_table}.{on}")
            
            JOIN = "\t\n".join(joins)

        return JOIN

    def get_columns(self, table:str) -> list:
        """
        Retrieves a list of `table` columns.

        :param table: Name of database table.
        :return: List of columns.
        """

        cursor = self.get_db().execute(f"SELECT * FROM {table} LIMIT 0")
        columns = [col[0] for col in cursor.description]

        return columns

    @staticmethod
    def _where(conditions) -> str:
        """
        Creates an SQL WHERE clause based on `conditions`.
        If conditions is an instance of:
            str: returns conditions
            dict: returns AND-joined series where 'key = val'
            list:
                if 1-D:
                    if size 3: joins elements of list
                    if size 2: joins elements of list with =
                if 2-D: recursively calls _where()

        :param conditions: A string, dict, or list of conditions.
        :return: String of SQL WHERE clause.
        """

        WHERE = ""
        if isinstance(conditions, str):
            WHERE = conditions
        elif isinstance(conditions, dict):
            WHERE += \
                " AND ".join([f"{key} = '{val}'" for key, val in conditions.items()]) #? val is always a string
        elif isinstance(conditions, list):
            if isinstance(conditions[0], list):
                WHERE += \
                    " AND ".join([LoreKeeper._where(condition for condition in conditions)])
            elif len(conditions) == 3:
                WHERE += " ".join(conditions)
            elif len(conditions) == 2:
                WHERE += " = ".join(conditions)
        
        return WHERE

    def select(self, table:str, columns:list=['*'], join=None, where=None, datatype=None) -> list:
        """
        SELECT `columns` FROM `table`
        """

        SELECT = "SELECT {columns}".format(columns=", ".join(columns))
        FROM = f"FROM {table}"
        JOIN = self._join(table, join)
        WHERE = f"WHERE {self._where(where)}" if where else ""

        results = self.get_db().execute("\n\t".join([SELECT, FROM, JOIN, WHERE])).fetchall()
        if datatype:
            results = [datatype.from_row(result) for result in results]

        return results

    #TODO: columns parameter 
    #? and maybe intersection of table columns and values
    def insert(self, table:str, values:dict) -> None:
        """
        INSERT INTO `table` VALUES (`values`)
        """

        INSERT = f"INSERT INTO `{table}`"
        cols = self.get_columns(table)[1:]
        COLUMNS = "({})".format(", ".join(cols))
        VALUES = "VALUES ({})".format(", ".join("?" * len(cols)))

        db = self.get_db()
        db.execute(
            " ".join([INSERT, COLUMNS, VALUES]),
            [f"{values.get(key)}" for key in cols]
        )
        db.commit()

    # def __repr__(self): pass