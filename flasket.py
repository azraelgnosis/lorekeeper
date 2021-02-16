from flask import Flask

from .auth import AuthPrint
from .lorekeeper import LoreKeeper

class Flasket(Flask):
    def __init__(self, import_name, db_name, **kwargs):
        super().__init__(import_name, **kwargs)

        self.lk = LoreKeeper(db_name)
        self.register_blueprint(AuthPrint(self.lk))
