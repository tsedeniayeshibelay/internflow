from flask import Flask

app = Flask(__name__)

app.secret_key = "internflow-development-key"

from app import routes