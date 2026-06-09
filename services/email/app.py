import os

from flask import Flask

from services.email.config import Config
from services.email.routes.health import health_bp
from services.email.routes.send import send_bp


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)

    testing = os.getenv("FLASK_TESTING") == "1"
    if not testing:
        config_class.validate()

    app.register_blueprint(health_bp)
    app.register_blueprint(send_bp)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("EMAIL_SERVICE_PORT", "5010"))
    app.run(debug=True, host="0.0.0.0", port=port)
