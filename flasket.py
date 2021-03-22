from flask import Flask
import os

from .auth import AuthPrint
from .lorekeeper import LoreKeeper
from .cyanotype import Rule

class Flasket(Flask):
    def __init__(self, import_name, lorekeeper=None, db_name=None, **kwargs):
        super().__init__(import_name.split(".")[0], **kwargs)

        self.lk = lorekeeper or LoreKeeper(db_name)
        self.paths = {
            "root": self.root_path,
            "instance": self.instance_path,
            "app": os.path.dirname(self.instance_path),
            "static": self.static_folder
        }
        self.paths["templates"] = os.path.join(self.paths['app'], self.template_folder)
        self.register_blueprint(AuthPrint(self.lk, self.paths['templates']))

    @property
    def url_rules(self):
        return [Rule(rule.rule, rule.endpoint, methods=rule.methods) for rule in self.url_map.iter_rules()]