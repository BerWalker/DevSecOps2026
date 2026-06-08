import os

from flask import Flask

from services.analytics.config import Config
from services.analytics.extensions import db, migrate
from services.analytics import models
from services.analytics.routes.campaign_analytics import campaign_analytics_bp
from services.analytics.routes.dashboard import dashboard_bp
from services.analytics.routes.tracking import tracking_bp


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    testing = os.getenv("FLASK_TESTING") == "1"
    if not testing:
        config_class.validate()

    db.init_app(app)
    migrate.init_app(app, db, directory="services/analytics/migrations")
    app.register_blueprint(tracking_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(campaign_analytics_bp)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("ANALYTICS_SERVICE_PORT", "5003"))
    app.run(debug=True, host="0.0.0.0", port=port)
