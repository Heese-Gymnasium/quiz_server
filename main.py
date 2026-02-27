import datetime

from flask import Flask, request, jsonify
import uuid
import json
import sqlite3
con = sqlite3.connect("quiz.db")
cur = con.cursor()

# driver = GraphDatabase.driver(URI, auth=AUTH)
    

app = Flask(__name__)


def init_db():
    # Create tables if they don't exist
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer1 TEXT NOT NULL,
            answer2 TEXT NOT NULL,
            answer3 TEXT NOT NULL,
            answer4 TEXT NOT NULL,
            correct_answer TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_answered_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            UNIQUE(username, question_id),
            FOREIGN KEY (username) REFERENCES users(username),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    con.commit()

def load_users_to_db():
    with open('users.csv', 'r') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) >= 2:
                username, password = parts[0], parts[1]
                try:
                    cur.execute('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', 
                               (username, password))
                except sqlite3.IntegrityError:
                    pass
    con.commit()

def load_questions_to_db():
    with open('questions.csv', 'r') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) >= 6:
                question = parts[0]
                answers = parts[1:5]
                correct_answer = parts[5]
                cur.execute('''
                    SELECT id FROM questions WHERE question = ?
                ''', (question,))
                if not cur.fetchone():
                    cur.execute('''
                        INSERT INTO questions (question, answer1, answer2, answer3, answer4, correct_answer)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (question, answers[0], answers[1], answers[2], answers[3], correct_answer))
    con.commit()

def mark_question_answered(username, question_id):
    try:
        cur.execute('''
            INSERT OR IGNORE INTO user_answered_questions (username, question_id)
            VALUES (?, ?)
        ''', (username, question_id))
        con.commit()
    except sqlite3.IntegrityError:
        pass

def has_user_answered_question(username, question_id):
    cur.execute('''
        SELECT id FROM user_answered_questions WHERE username = ? AND question_id = ?
    ''', (username, question_id))
    return cur.fetchone() is not None

# Initialize database and load data
init_db()
load_users_to_db()
load_questions_to_db()

# Für jeden Request muss noch die Session geprüft werden!
# TODO: Datenbank-Funktionnen bauen

def authenticate(request):
    sid = request.headers.get('Session-ID')
    if not sid or not check_session(sid):
        raise Exception("Unauthorized")

def identify(username, password):
    with open('users.csv', 'r') as f:
        for line in f:
            parts = line.strip().split(';')
            if parts[0] == username and parts[1] == password:
                return True
    return False
    # TODO: Datenbank nutzen

def gen_session_id(username, timestamp):
    session_data = {
        "username": username,
        "sid": str(uuid.uuid4()),
        "timestamp": timestamp.isoformat()
    }
    with open('session.json', 'a') as f:
        json.dump(session_data, f)
        f.write('\n')
    # TODO: Session in Datenbank speichern
    return session_data['sid']

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
    authenticate(request)
    question = get_question_by_id(2)
    question.pop('correct_answer', None)
    print(f"Sending question: {question}")
    return jsonify({"status": "success", "question": question}), 200

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    authenticate(request)
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
    # try:
        print(request.data)
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        print(f"Login attempt for user: {username}")
        # Daten mit users.csv ableichen
        if identify(username, password):
            sid = gen_session_id(username, datetime.datetime.now())
            return jsonify({"status": "success", "sid": sid}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    # except Exception as e:
    #     return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/logout', methods=['POST'])
def logout():
    authenticate(request)
    try:
        data = request.get_json()
        username = data.get('username')
        print(f"Logout attempt for user: {username}")
        # Session löschen
        with open('session.json', 'r') as f:
            sessions = [json.loads(line) for line in f]
        sessions = [s for s in sessions if s['username'] != username]
        with open('session.json', 'w') as f:
            for session in sessions:
                json.dump(session, f)
                f.write('\n')
        return jsonify({"status": "success", "message": "Logout successful"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


def check_session(sid):
    with open('session.json', 'r') as f:
        sessions = [json.loads(line) for line in f]
    for session in sessions:
        if session['sid'] == sid:
            return True
    return False


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)