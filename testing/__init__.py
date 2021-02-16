from flask import Flask, render_template
import os

from ..flasket import Flasket

PATH = os.path.dirname(__file__)

def create_app():
    app = Flasket(import_name=__name__, instance_path=os.path.join(PATH, "instance"), 
            db_name="DATABASE")

    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, 'db.sqlite'),
        SECRET_KEY="dev"
    )

    @app.route('/')
    def index(): return render_template("index.html")

    app.lk.init_app(app)

    return app
