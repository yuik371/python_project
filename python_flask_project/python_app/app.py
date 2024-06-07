from flask import Flask, render_template, request, jsonify, send_from_directory # Importing necessary modules from Flask 
from pymongo import MongoClient # Used for MongoDB operations 
from bson import ObjectId, json_util # Handling BSON data, specifically for ObjectId
import nbformat # For reading and writing Jupyter notebooks 
import json # For JSON operations 
import matplotlib 
matplotlib.use('Agg') # Setting matplotlib to use the 'Agg' backend for non-GUI environments
import matplotlib.pyplot as plt # For creating plots

# Creating a Flask application instance 
app = Flask(__name__)

# MongoDB configuration 
client = MongoClient('mongodb://localhost:27017/') # Connecting to the MongoDB Server 
db = client['car_recalls'] # Selecting the 'car_recalls' database
collection = db['recalls'] # Selecting the 'recalls' collection

# Helper class to enable JSON serialization of ObjectId
class JSONEncoder(json.JSONEncoder):
  def default(self, o):
    if isinstance(o, ObjectId):
      return str(o) # Converts ObjectId to string
    return json_util.default(o)

# Defines a route for loading Jupyter notebooks
@app.route('/api/recalls/load_notebook', methods=['POST']) 
def load_notebook():
  file_path = request.json['file_path'] # Extracts the file path from the POST request
  with open(file_path, 'r', encoding='utf-8') as f: # Opens the file
    notebook = nbformat.read(f, as_version=4) # Reads the notebook file
   
  # Saves the Jupyter notebook data to MongoDB
  notebook_id = collection.insert_one(notebook).inserted_id
  return jsonify({'status': 'success', 'notebook_id': str(notebook_id)})

@app.route('/api/recalls/graph', methods=['GET']) # Route for serving the graph page
def graph_page():
  return send_from_directory('static', 'graph.html') # Serves the 'graph.html' from the 'static' directory

@app.route('/api/recall_counts', methods=['GET']) # Route for getting recall counts
def get_recall_counts():
  pipeline = [
    {
      "$match": {
        "recall.status": "active" # Matches documents where recall status is active
      }
    },
    {
      "$group": {
        "_id": "$manufacturer", # Groups by manufacturer
        "recallCount": {"$sum": 1} # Counts the number of recalls
      }
    },
    {
      "$sort": {"recallCount": -1} # Sorts the results by recall count in descending order
    }
  ]

  results = db.products.aggregate(pipeline) # Executes the aggregation pipeline

  # Converts the results to a list and returns them in JSON format
  return jsonify(list(results))

# Route for recall visualizations
@app.route('/api/recalls/visualization', methods=['GET']) 
def visualize_recalls():
  pipeline = [
    {"$group": {"_id": "$제작자", "리콜횟수": {"$sum": 1}}}, # Groups by manufacturer and counts recalls
    {"$sort": {"리콜횟수": -1}} # Sorts by recall count in descending order
  ]

  # Executes the aggregation pipeline
  results = db.recalls.aggregate(pipeline) 

  manufacturers = [result['_id'] for result in results] # Extracts manufacturers
  recall_counts = [result['리콜횟수'] for result in results] # Extracts recall counts

  plt.figure(figsize=(10, 6)) # Creates a figure
  plt.bar(manufacturers, recall_counts, color='skyblue') # Creates a bar plot
  plt.xlabel('제작자') # Sets the x-axis label
  plt.ylabel('리콜 횟수') # Sets the y-axis label
  plt.title('제작자별 리콜 횟수') # Sets the title of the plot
  plt.xticks(rotation=45) # Rotates the x-axis labels

  # Saves the plot as an image file
  plt.savefig('static/recalls_visualization.png')
  plt.close() # Closes the plot

  # Returns the URL of the saved image file
  return send_from_directory('static', 'recalls_visualization.png')

# Default route 
@app.route('/')
def home():
    return render_template('index.html') # Renders the 'index.html' template

# Route for managing recalls
@app.route('/api/recalls', methods=['GET', 'POST']) 
def manage_recalls():
  if request.method == 'POST': 
    recall_data = request.json # Gets recall data from POST request
    recall_id = collection.insert_one(recall_data).inserted_id # Inserts recall data into MongoDB
    return jsonify({'status': 'success', 'recall_id': str(recall_id)})
  else:
    recalls = list(collection.find()) # Fetches all recalls from MongoDB
    # Encodes the recalls into JSON format
    return Response(JSONEncoder().encode(recalls), mimetype="application/json")
      
if __name__ == '__main__':
    app.run(port=5000) # Runs the Flask application
