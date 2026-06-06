import os

from flask import Flask

from services.campaign.config import Config
from services.campaign.extensions import db, migrate
from services.campaign import models
from services.campaign.routes.campaigns import campaigns_bp
from services.campaign.routes.tracking import tracking_bp


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    testing = os.getenv("FLASK_TESTING") == "1"
    if not testing:
        config_class.validate()

    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(tracking_bp)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("CAMPAIGN_SERVICE_PORT", "5002"))
    app.run(debug=True, host="0.0.0.0", port=port)
