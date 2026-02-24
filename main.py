from flask import Flask, request, jsonify
import users
import uuid
# from neo4j import GraphDatabase, RoutingControl


URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "password")

# driver = GraphDatabase.driver(URI, auth=AUTH)
    

app = Flask(__name__)

# Für jeden Request muss noch die Session geprüft werden!

def gen_session_id():
    return str(uuid.uuid4())

def get_question_by_id(question_id):
    with open('questions.csv', 'r') as f:
        for i, line in enumerate(f):
            if i == question_id:
                parts = line.strip().split(';')
                return {
                    "id": question_id,
                    "question": parts[0],
                    "answers": parts[1:5],
                    "correct_answer": parts[5]
                }
        return None

@app.route('/api/get_next_question', methods=['GET'])
def get_next_question():
    # Vorerst Testfrage
    question = get_question_by_id(2)
    question.pop('correct_answer', None)
    print(f"Sending question: {question}")
    return jsonify({"status": "success", "question": question}), 200

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        answer = data.get('answer')
        print(f"Received answer for question {question_id}: {answer}")
        question = get_question_by_id(question_id)
        if not question:
            return jsonify({"status": "error", "message": "Question not found"}), 404
        correct_answer = question.get('correct_answer')
        if answer == correct_answer:
            return jsonify({"status": "success", "message": "Correct answer!"}), 200
        else:
            return jsonify({"status": "success", "message": "Wrong answer!"}), 200
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