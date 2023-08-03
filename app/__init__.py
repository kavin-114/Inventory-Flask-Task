# run.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.routes import app as routes_app

# Create the Flask app instance
app = Flask(__name__)

# Register the routes blueprint
app.register_blueprint(routes_app)

# Configuration
# app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a secure random key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Kavin%4011@localhost:3306/inventory'  # Replace with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking modifications for SQLAlchemy

# Create the SQLAlchemy database instance
from app.models import db
db.init_app(app)

from app import routes

migrate = Migrate(app, db)

