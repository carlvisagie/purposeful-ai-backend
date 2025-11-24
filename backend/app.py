from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

from flask_jwt_extended import JWTManager
from config import Config
from backend.models import db
import logging
from datetime import timedelta

# BLUEPRINT IMPORTS (FIXED FOR RENDER)
from backend.blueprints.auth import auth_bp
from backend.blueprints.api import api_bp
from backend.blueprints.admin import admin_bp
from backend.blueprints.coach import coach_bp
from backend.blueprints.onboarding import onboarding_bp
from backend.blueprints.webhooks import webhooks_bp
from backend.blueprints.dashboard import dashboard_bp
from backend.blueprints.health import health_bp
from backend.blueprints.admin_extended import admin_extended_bp


def create_app(config_class=Config):
    app = Flask(__name__)

    config = config_class.from_env()
    config.validate()

    app.config['SECRET_KEY'] = config.secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = config.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = config.jwt_secret_key
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)

    if not config.debug:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # REGISTER BLUEPRINTS (FIXED)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(coach_bp, url_prefix='/coach')
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_extended_bp)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return "✅ Purposeful Live API is running."

    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500

    return app


# WSGI ENTRYPOINT FOR RENDER + GUNICORN
app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

