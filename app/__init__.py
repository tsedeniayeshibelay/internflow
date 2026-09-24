from flask import Flask

app = Flask(__name__)

app.secret_key = "internflow-development-key"

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

from app import routes