import jinja2
import os
from flask import flash, g, session, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from lorekeeper.lorekeeper.cyanotype import Cyanotype
from lorekeeper.lorekeeper.consts import *
from lorekeeper.lorekeeper.models import User


class AuthPrint(Cyanotype):
    root_path = os.path.dirname(__file__)
    template_path = os.path.join(root_path, "templates") # same as template_folder?
    # auth_path = os.path.join(template_path, "auth")

    def __init__(self, lorekeeper:'LoreKeeper', template_folder:str, name:str='auth', import_name:str=__name__, url_prefix:str='/auth', **kwargs):
        self.url_rules = [
            {RULE:'/register/', ENDPOINT:'register', VIEW_FUNC:self.signup},
            {RULE:'/login/', ENDPOINT:'login', VIEW_FUNC:self.login},
            {RULE:'/logout/', ENDPOINT:'logout', VIEW_FUNC:self.logout},
        ]
        super().__init__(lorekeeper=lorekeeper, template_folder=self.template_path, name=name, import_name=import_name, url_prefix=url_prefix, **kwargs)
        self.jinja_loader = jinja2.FileSystemLoader([self.template_folder, template_folder])
        self.before_app_request(self.load_logged_in_user)

    def get_index(self):
        endpoint = ""
        for rule in self.lk.url_map.iter_rules():
            if "index" in rule.endpoint:
                endpoint = rule.endpoint
                break
        return endpoint

    # ====================================================================================================
    # views
    # ====================================================================================================

    def signup(self):
        if request.method == "POST":
            username = request.form['username'].strip().lower()
            password = request.form['password'].strip()

            errors = []
            if self.username_exists(username):
                errors.append(f"User '{username}' already exists.")
            if not password:
                errors.append("Must include password.")

            if not errors:
                hashed_password = generate_password_hash(password)
                self._register_user(username, hashed_password)

                return self._login(username, password)

            flash(errors)

        return render_template('auth/auth.html', menu="register", layout=self.lk.paths['layout'])

    def login(self):
        if request.method == "POST":
            username = request.form['username']
            password = request.form['password']

            return self._login(username, password)            

        return render_template('auth/auth.html', menu="login", layout=self.lk.paths['layout'])

    def _login(self, username, password):
        errors = []
        user = self._get_user_by_val(username)
        if not user:
            errors.append(f"User '{username}' doesn't exist.")
        elif not check_password_hash(user.password, password):
            errors.append("Password is incorrect.")
        
        if not errors:
            session.clear()
            session[USER_ID] = user.id

            index = self.get_index()
            return redirect(url_for(index))

        flash(errors)

    def logout(self):
        session.clear()
        index = self.get_index()
        return redirect(url_for(index))

    # ====================================================================================================

    def _get_user_by_id(self, user_id:int) -> User:
        return self.lk.select(Tables.USER, where={USER_ID: user_id}, datatype=User)[0]

    def _get_user_by_val(self, user_val:str) -> User:
        return self.lk.select(Tables.USER, where={USER_VAL: user_val}, datatype=User)[0]

    def username_exists(self, user_val:str) -> bool:
        return bool(self.lk.select(Tables.USER, columns=[USER_VAL], where={USER_VAL: user_val}))
        
    #? Is this needed?
    @classmethod
    def get_usernames(cls) -> list: return cls.select(Tables.USER, columns=[USER_VAL])

    def _register_user(self, user_val:str, password:str) -> None:
        new_user = User(user_val=user_val, password=password)
        self.lk.insert(Tables.USER, values=new_user.to_dict())

    def load_logged_in_user(self) -> None:
        user_id = session.get('user_id')

        if not user_id:
            g.user = None
        else:
            try:
                g.user = self._get_user_by_id(user_id)
            except IndexError:
                g.user = None
                session.clear()
                redirect(url_for('auth.login'))


# ===========================

# TODO
# import functools
        
# def login_required(view):
#     @functools.wraps(view)
#     def wrapped_view(**kwargs):
#         if g.user is None:
#             return redirect(url_for('auth.login'))
        
#         return view(**kwargs)
    
#     return wrapped_view
