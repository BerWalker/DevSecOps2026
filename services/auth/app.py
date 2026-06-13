import os

from flask import Flask

from services.auth.config import Config
from services.auth.extensions import db, migrate
from services.auth import models
from services.auth.routes.auth import auth_bp
from services.auth.routes.internal import internal_bp


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    testing = os.getenv("FLASK_TESTING") == "1"
    if not testing:
        config_class.validate()

    db.init_app(app)
    migrate.init_app(app, db, directory="services/auth/migrations")
    app.register_blueprint(auth_bp)
    app.register_blueprint(internal_bp)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("AUTH_SERVICE_PORT", "5001"))
    app.run(debug=True, host="0.0.0.0", port=port)
