from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
import logging
from datetime import timedelta

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
    
    from blueprints.auth import auth_bp
    from blueprints.api import api_bp
    from blueprints.admin import admin_bp
    from blueprints.coach import coach_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(coach_bp, url_prefix='/coach')
    
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

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=app.config.get('DEBUG', False))
