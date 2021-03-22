from flask import Blueprint, current_app

from lorekeeper.lorekeeper.consts import *


class Rule(object):
    def __init__(self, rule:str, endpoint:str, view_func=None, methods:tuple=None):
        self.rule = rule
        self.endpoint = endpoint
        self.view_func = view_func
        self.methods = methods or (GET, POST)

    def __iter__(self): return iter(self.to_dict().items())
    def __repr__(self): return f"Rule '{self.rule}' {str(self.methods)} -> {self.endpoint}"

    def to_dict(self):
        return {
            "rule": self.rule,
            "endpoint": self.endpoint,
            "view_func": self.view_func,
            "methods": self.methods
        }


class Cyanotype(Blueprint):
    url_rules = []

    def __init__(self, lorekeeper:"LoreKeeper", name:str, import_name:str, **kwargs):
        super().__init__(name=name, import_name=import_name.split(".")[0], **kwargs)
        self.lk = lorekeeper
        self.add_rules()
        self._app = None

    def __repr__(self): return f"{self.__class__.__name__}: {self.name}"

    @property
    @staticmethod
    def app(): return current_app

    def add_rules(self) -> None:
        for rule in self.url_rules:
            self.add_url_rule(**dict(Rule(**rule)))  # hm...

    @staticmethod
    def filter_form(form:dict) -> dict:
        return dict(filter(lambda kv: kv[1], form.items()))
