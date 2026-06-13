from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify(
        {
            "status": "info",
            "message": (
                "This file is a legacy stub. Use Docker Compose "
                "(docker compose up) to run the microservices stack."
            ),
            "gateway": "http://localhost:5000",
        }
    ), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
