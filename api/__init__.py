from flask import Flask, jsonify

try:
    from flask_cors import CORS
except ImportError:  # pragma: no cover - optional at import time
    CORS = None


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    if CORS is not None:
        CORS(app)

    @app.get("/api/v1/health")
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "vendor-dashboard-api"})

    # Register blueprints only when their modules can load cleanly.
    optional_blueprints = [
        ("vendors", "vendors_bp"),
        ("performance", "performance_bp"),
        ("alerts", "alerts_bp"),
    ]
    for module_name, blueprint_name in optional_blueprints:
        try:
            module = __import__(f"api.{module_name}", fromlist=[blueprint_name])
            app.register_blueprint(getattr(module, blueprint_name))
        except Exception:
            continue

    return app


app = create_app()
