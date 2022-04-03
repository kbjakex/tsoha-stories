from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv

def _get_db_uri():
    db_uri = getenv("DATABASE_URL")
    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    return db_uri

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = _get_db_uri()
db = SQLAlchemy(app)
