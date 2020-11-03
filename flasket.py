from flask import Flask

from .auth import AuthView

class Flasket(Flask):
    def __init__(self):
        super().__init__()

        self.add_url_rule('/register/', view_func=AuthView.as_view('register'), template_name='register.html')
        self.add_url_rules(AuthView.url_rules)

    def add_url_rules(self, rules:list):
        for rule in rules:
            self.add_url_rule()
