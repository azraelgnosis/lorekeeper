from flask import flash, render_template, request, session
from flask.views import View
from werkzeug.security import check_password_hash, generate_password_hash

from .consts import *
from .models import User
from .lorekeeper import LoreKeeper

class AuthView(View):
    url_rules = {
        
    }

    def __init__(self, lorekeeper:LoreKeeper, template_name:str):
        self.lk = lorekeeper
        self.template_name = template_name

    def dispatch_request(self):
        pass

    @classmethod
    def register(cls):
        if request.method == POST:
            username = request.form[USERNAME].strip().lower()
            password = request.form[PASSWORD].strip()
            password = generate_password_hash(password)

            error = None
            if username := cls.username_exists(username):
                error = f"User {username} already exists."
            
            if not error:
                cls.register_user(username, password)

            flash(error)

        return render_template('auth/register.html')

    @staticmethod
    def login(): ...

    @staticmethod
    def logout():
        session.clear()
        return redirect(url_for('index'))  #! may need to be a variable

    def username_exists(self, username:str) -> bool:
        return bool(self.lk.select(Tables.USER, columns=[USERNAME], where={USERNAME: username}))

    def register_user(self, username, password):
        new_user = User(username, password)
        self.lk.insert(Tables.User, values=new_user.to_dict())

from flask import Flask
app = Flask()
app.add_url_rule('/register/', view_func=AuthView.as_view('register'), template_name='register.html')



# ========================================================

from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth')


# ========================================



from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import functools

bp = Blueprint('auth', __name__, url_prefix='/auth')
        
@bp.route('/login/', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user(username)

        error = None
        if not user:
            error = "User doesn't exist."
        elif not check_password_hash(user.password, password):
            error = "Password is incorrect."
        
        if not error:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for("dem3.dashboard"))
        
        flash(error)

    return render_template('auth/login.html')

@bp.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('dem3.index'))

@bp.before_app_request
def load_logged_in_user():
    """
    """

    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_user(user_id)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)
    
    return wrapped_view

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import functools
from werkzeug.security import check_password_hash, generate_password_hash

#from dem3_multi.db import get_db, get_user, get_usernames, select, insert
from foundry.db import DataManager

bp = Blueprint('auth', __name__, url_prefix='/auth')

dm = DataManager()

def username_exists(username:str) -> bool:
    db = dm.get_db()

    query = "SELECT username FROM users " \
        "WHERE username = ?"

    return bool(db.execute(query, (username,)).fetchone())

@bp.route('/login/', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = dm.get_user(username)

        error = None
        if not user:
            error = "User doesn't exist."
        elif not check_password_hash(user.password, password):
            error = "Password is incorrect."

        if not error:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for("dem3.dashboard"))

        flash(error)

    return render_template('auth/login.html')

@bp.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('dem3.index'))

@bp.before_app_request
def load_logged_in_user():
    """
    """

    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = dm.get_user(user_id)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view