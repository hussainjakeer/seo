import os
from flask import Flask
from dotenv import load_dotenv
from datetime import timedelta
from flask_session import Session



dotenv_path = 'config.env'
load_dotenv(dotenv_path) 

app = Flask(__name__)

# Flask session configuration
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem for storing session data
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')  # Directory to store session files
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_USE_SIGNER'] = True  # Sign the session cookies
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=300)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
# app.config['WEB_CREDS'] = os.getenv('web_creds')

Session(app)


from app.routes import default_routes, gsc_api_auth

# Ensure the flask_session directory exists
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])