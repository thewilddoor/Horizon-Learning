# app/__init__.py

from flask import Flask, render_template
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
scheduler = APScheduler()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    csrf.init_app(app)
    login.login_view = 'auth.login'  # Ensure this points to your login route
    
    # Import models to register them with SQLAlchemy
    with app.app_context():
        from . import models  # Import models here
    
    # Register blueprints
    from app.routes import auth
    app.register_blueprint(auth)
    
    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app
