from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

import routes