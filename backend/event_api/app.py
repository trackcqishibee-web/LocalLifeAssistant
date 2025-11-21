from flask import Flask
from .config import Config
from .limiter import limiter
from .routes import api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    limiter.init_app(app)
    
    app.register_blueprint(api_bp)
    
    return app
