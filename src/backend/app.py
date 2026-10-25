from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "backend"})

@app.route("/api/items")
def items():
    return jsonify([{"id": 1, "name": "item-one"}, {"id": 2, "name": "item-two"}])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)