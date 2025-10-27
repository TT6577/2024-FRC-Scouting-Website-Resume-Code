from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path

db = SQLAlchemy()
DB_NAME = "databasenew.db"


def create_app():
  app = Flask(__name__)
  app.config['SECRET_KEY'] = 'FRC'

  #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{DB_NAME}'
  #stores database in folder

  # Change the database url to the database to the one you need. Ex. 'sqlite:///{database name here}.db'. You need to create a new .db file by pressing new file and naming it {name}.db first, though
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DBtest2.db'

  db.init_app(app)

  from .auth import auth
  app.register_blueprint(auth, url_prefix='/')

  from .models import Scout
  with app.app_context():
    db.create_all()

  return app
