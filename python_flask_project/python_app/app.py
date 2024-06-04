from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['car_recalls']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recalls', methods=['GET'])
def get_recalls():
    recalls = db.python_project.find({}, {'_id': False})
    result = list(recalls)
    return render_template('recalls.html', recalls=result)

if __name__ == '__main__':
    app.run(port=5000)
