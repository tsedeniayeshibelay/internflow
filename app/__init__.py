import os

from flask import Flask

from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


from app import routes