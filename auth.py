from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .consts import *
from .models import User

class AuthPrint(Blueprint):
    url_rules = []

    def __init__(self, lorekeeper:'LoreKeeper', name:str='auth', import_name:str=__name__, url_prefix:str='/auth', **kwargs):
        super().__init__(name=name, import_name=import_name, url_prefix=url_prefix, **kwargs)
        self.lk = lorekeeper

        for url_rule in self.url_rules:  # TODO
            pass

        # TODO
        self.add_url_rule(rule='/register/', endpoint='register', view_func=self.signup, methods=(GET, POST))
        self.add_url_rule(rule='/login/', endpoint='login', view_func=self.login, methods=(GET, POST))
        self.add_url_rule(rule='/logout/', endpoint='logout', view_func=self.logout, methods=(GET, POST))
        self.before_app_request(self.load_logged_in_user)

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

        return render_template('auth.html', menu="register")

    def login(self):
        if request.method == "POST":
            username = request.form['username']
            password = request.form['password']

            return self._login(username, password)            

        return render_template('auth.html', menu="login")

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

            return redirect(url_for('index'))

        flash(errors)

    @staticmethod
    def logout():
        session.clear()
        return redirect(url_for('index'))  #! may need to be a variable

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
            g.user = self._get_user_by_id(user_id)


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
