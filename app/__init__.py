import os
from os.path import join
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from flask_migrate import Migrate

basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
mysql = MySQL()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY") or 'prc9FWjeLYh_KsPGm0vJcg',
        SQLALCHEMY_DATABASE_URI='mysql+pymysql://root:passer@localhost/game',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEBUG=True,
        UPLOAD_FOLDER=join(basedir, 'static/files')
    )

    db.init_app(app)
    migrate.init_app(app, db)

    from app.auth.views import auth
    from app.main.views import main
    app.register_blueprint(auth)
    app.register_blueprint(main)

    from app.main.errors import page_not_found
    app.register_error_handler(404, page_not_found)

    return app