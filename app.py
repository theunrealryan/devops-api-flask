from flask import Flask, jsonify, request
app = Flask(__name__)

tasks = []

@app.route("/tasks", methods=["GET"])
def list_tasks():
    return jsonify(tasks)

@app.route("/tasks", methods=["POST"])
def add_task():
    tasks.append(request.json)
    return {"msg": "ok"}, 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
