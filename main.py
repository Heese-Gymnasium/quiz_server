from flask import Flask, request, jsonify
import users
import uuid
from neo4j import GraphDatabase, RoutingControl


URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "password")

driver = GraphDatabase.driver(URI, auth=AUTH)
    

app = Flask(__name__)

# Für jeden Request muss noch die Session geprüft werden!

def gen_session_id():
    return str(uuid.uuid4())

@app.route('/api/data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        return jsonify({"status": "success", "message": "Data received"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/get_next_question', methods=['GET'])
def get_next_question():
    # Vorerst Testfrage
    question = {
        "id": 1,
        "text": "What is the capital of France?",
        "options": ["Paris", "London", "Berlin", "Madrid"]
    }
    return jsonify({"status": "success", "question": question}), 200

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        answer = data.get('answer')
        print(f"Received answer for question {question_id}: {answer}")
        # Richtige Antwort zurückgeben
        return jsonify({"status": "success", "message": "Answer submitted"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        print(f"Login attempt for user: {username}")
        # Daten mit users.csv ableichen
        if users.authenticate(username, password):
            return jsonify({"status": "success", "message": "Login successful"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        data = request.get_json()
        username = data.get('username')
        print(f"Logout attempt for user: {username}")
        # Session löschen
        return jsonify({"status": "success", "message": "Logout successful"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


def check_session():
    return True


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)