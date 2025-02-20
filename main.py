import os
from flask import Flask, render_template
import json

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


# Function to load JSON data
def load_json(question_file):
    try:
        file_path = os.path.join(DATA_DIR, f"{question_file}.json")  # Correct path resolution
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as err:
        print(f"Error reading or parsing the JSON file: {err}")
        raise


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/menu')
def menu():
    return render_template('menu.html')


@app.route('/icebreaker')
def icebreaker():
    questions = load_json('questions')
    ice_level = next((level for level in questions["levels"] if level["name"] == "ice breaker"), None)
    ice_questions = ice_level["questions"] if ice_level else []
    return render_template('ice.html', question=ice_questions)


@app.route('/confess')
def confess():
    questions = load_json('questions')
    confess_level = next((level for level in questions["levels"] if level["name"] == "confess"), None)
    confess_questions = confess_level["questions"] if confess_level else []
    return render_template('confess.html', question=confess_questions)


@app.route('/deep')
def deep():
    questions = load_json('questions')
    deep_level = next((level for level in questions["levels"] if level["name"] == "deep"), None)
    deep_questions = deep_level["questions"] if deep_level else []
    return render_template('deep.html', question=deep_questions)


if __name__ == '__main__':
    app.run(debug=True, port=3000)
