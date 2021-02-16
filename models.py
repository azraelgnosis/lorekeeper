from abc import ABC
import json
import sqlite3

from .consts import *

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


class Model(ABC, object):
    __slots__ = [ID, NAME]
    columns = []
    rename = {}

    def __init__(self, pk=None, name=None, **kwargs) -> None:
        self.id = pk
        self.name = name  # TODO what's this for?

        for key, val in kwargs.items():
            setattr(self, key, val)
        
        self._init()
    
    def _init(self): ...

    @classmethod
    def from_row(cls, row:Row) -> 'Model':
        if any(key in cls.rename.keys() for key in row.keys()):
            new_obj = cls(**{cls.rename.get(key, key): val for key, val in row.items()})
        else:
            new_obj = cls(**row)

        return new_obj

    def to_csv(self): return ",".join(getattr(self, slot) for slot in self.__slots__)
    def to_dict(self): return dict(self)
    def to_json(self): return json.dumps(dict(self)) # return str(dict(self)).replace("'", '"').replace("None", "null")

    def __iter__(self): return iter({slot: getattr(self, slot) for slot in self.__slots__}.items())
    def __repr__(self): return f"{self.__class__.__name__}: {self.name}"


class Table(Model):
    __slots__ = ['db', 'name']
    def __init__(self, name:str, db:sqlite3.Connection) -> None:
        self.name = name
        self.db = db

        self._columns = []
        self._rows = []
        self._size = None

    @property
    def columns(self) -> list:
        """Retrieves the table columns from the database and assigns them to `self.columns` as a list."""

        if not self._columns:
            cursor = self.db.execute(f"SELECT * FROM {self.name}")
            self._columns = [col[0] for col in cursor.description]

        return self._columns

    @property
    def rows(self) -> list:
        if not self._rows:
            raise NotImplementedError

    @property
    def size(self) -> int:
        """Retrieves the number of rows from database and assigns that to `self.size`."""

        if not self._size:
            self._size = self.db.execute(
                    f"SELECT COUNT(*) AS count FROM {self.name}"
                ).fetchone()['count']
        
        return self._size

    def __len__(self): return self.size
    def __repr__(self): return f"{self.name}: {', '.join(self.columns)}"


class User(Model):
    __slots__ = [USER_ID, USER_VAL, PASSWORD]

    def __init__(self, user_id:int=None, user_val:str=None, password:str=None):
        super().__init__(id=user_id, name=user_val)
        self.user_id = user_id
        self.user_val = user_val
        self.password = password
