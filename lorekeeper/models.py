from abc import ABC
import json
import sqlite3

from lorekeeper.lorekeeper.consts import *

class Row(sqlite3.Row):
    def __init__(self, cursor, values):
        self.cursor = cursor
        self.values = values
        self.columns = (col[0] for col in cursor.description)
        
        self._id = None
        self._val = None
        
        for col, val in zip(self.columns, self.values):
            setattr(self, col, val)

    @property
    def id(self): 
        if not self._id:
            self._id = next(val for col, val in zip(self.columns, self.values) if 'id' in col)
        return self._id

    @property
    def val(self):
        if not self._val:
            self._val = next(val for col, val in zip(self.columns, self.values) if 'val' in col)
        return self._val

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
    __slots__ = [ID, VAL]
    columns = []
    aliases = {}

    def __init__(self, pk=None, val=None, **kwargs) -> None:
        self.id = pk
        self.val = val

        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot))

        for alias, attr in self.aliases.items():
            setattr(self, alias, self[attr])

    @classmethod
    def from_row(cls, row:Row) -> 'Model': return cls(**row)

    def to_csv(self): return ",".join(getattr(self, slot) for slot in self.__slots__)
    def to_dict(self): return {slot: getattr(self, slot) for slot in self.__slots__}
    def to_json(self): return json.dumps(self.to_dict()) # return str(dict(self)).replace("'", '"').replace("None", "null")

    def __repr__(self): return f"{self.__class__.__name__}: {self.val}"

    def __getitem__(self, attr:str): return getattr(self, attr)


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
        super().__init__(pk=user_id, val=user_val)
        self.user_id = user_id
        self.user_val = user_val
        self.password = password
