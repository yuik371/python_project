from flask import Flask, render_template, request, jsonify, send_from_directory, render_template # Importing necessary modules from Flask 
from pymongo import MongoClient, errors # Used for MongoDB operations 
from bson import ObjectId, json_util # Handling BSON data, specifically for ObjectId
import nbformat # For reading and writing Jupyter notebooks 
import json # For JSON operations 
import matplotlib 
matplotlib.use('Agg') # Setting matplotlib to use the 'Agg' backend for non-GUI environments
import matplotlib.pyplot as plt # For creating plots
import os

# Creating a Flask application instance 
app = Flask(__name__)

# MongoDB configuration 
MONGO_URI = os.getenv('MONGO_URL', 'mongodb://localhost:27017/') # Connecting to the MongoDB Server 
DB_NAME = os.getenv('DB_NAME', 'car_recalls') # Selecting the 'car_recalls' database
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'recalls') # Selecting the 'recalls' collection

  # Attempt to connect to MongoDB
try: 
    # Use MongoClient to connect to the MongoDB server with the provided MONGO_URI
    client = MongoClient(MONGO_URI) # MONGO_URI -> localhost:27017
    
    # Select the specified database using the client
    db = client[DB_NAME] # DB_NAME -> car_recalls
    
    # Select the specified collection from the database
    collection = db[COLLECTION_NAME]  # COLLECTION_NAME -> recalls
except errors.ConnectionFailure as e:
    # If connection fails, print an error message
    print(f"Could not connect to MongoDB: {e}")

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
    {"$match": {"recall.status": "active"}},
    {"$group": {"_id": "$manufacturer", "recallCount": {"$sum": 1}}},
    {"$sort": {"recallCount": -1}}
  ]
  results = db.products.aggregate(pipeline) # Executes the aggregation pipeline
  # Converts the results to a list and returns them in JSON format
  return jsonify(list(results))
except Exception as e:
  return jsonify({'status': 'error', 'message': str(e)}), 400

# Route for recall visualizations
@app.route('/api/recalls/visualization', methods=['GET']) 
def visualize_recalls():
  pipeline = [
    {"$group": {"_id": "$제작자", "리콜횟수": {"$sum": 1}}}, # Groups by manufacturer and counts recalls
    {"$sort": {"리콜횟수": -1}} # Sorts by recall count in descending order
  ]

  # Executes the aggregation pipeline
  results = db.recalls.aggregate(pipeline) 

  # Log results for debugging
  print(f"Results: {results}")

  if not results:
    return jsonify({'status': 'error', 'message': 'No data available for visualization'}), 400
  manufacturers = [result['_id'] for result in results] # Extracts manufacturers
  recall_counts = [result['리콜횟수'] for result in results] # Extracts recall counts

  # Check: Verify if the manufacturers and recall_counts lists are empty
  if len(manufacturers) == 0 or len(recall_counts) == 0:
    # If either list is empty, notify the client that there is no data available for visualization
    return jsonify({'status': 'error', 'message': 'No data available for visualization'}), 400
  
  plt.figure(figsize=(10, 6)) # Creates a figure
  plt.bar(manufacturers, recall_counts, color='skyblue') # Creates a bar plot
  plt.xlabel('제작자') # Sets the x-axis label
  plt.ylabel('리콜 횟수') # Sets the y-axis label
  plt.title('제작자별 리콜 횟수') # Sets the title of the plot
  plt.xticks(rotation=45) # Rotates the x-axis labels

  # Define the directory to save the static files
  static_dir = os.path.join(os.getcwd(), 'static')

  # Check if the directory exists
  if not os.path.exists(static_dir):
    # If the directory does not exist, create it
    os.makedirs(static_dir)

  # Save the plot as a PNG file in the static directory
  plt.savefig(os.path.join(static_dir, 'recalls_visualization.png'))

  # Close the plot to free up memory
  plt.close()

  # Return the saved PNG file from the static directory
  return send_from_directory(static_dir, 'recalls_visualization.png')

# If any exception occurs, catch it and return an error message
except Exception as e:
  # Return a JSON error message and a 400 HTTP status code
  return jsonify({'status': 'error', 'message': str(e)}), 400

# Route for managing recalls
@app.route('/api/recalls', methods=['GET', 'POST'])
def manage_recalls():
    # Handle POST request
    if request.method == 'POST': 
        # Receive recall data as JSON from the request
        recall_data = request.json
        try:
            # Insert the recall data into the database and return the inserted document's ID
            recall_id = collection.insert_one(recall_data).inserted_id
            # If insertion is successful, return a success message and the recall ID in JSON format
            return jsonify({'status': 'success', 'recall_id': str(recall_id)})
        except Exception as e:
            # In case of an exception, return an error message in JSON format with HTTP status code 400
            return jsonify({'status': 'error', 'message': str(e)}), 400
    else:
        # Handle GET request
        try:
            # Query all recall data from the database
            recalls = list(collection.find())
            # Encode the queried data to JSON format and return it
            return Response(JSONEncoder().encode(recalls), mimetype="application/json")
        except Exception as e:
            # In case of an exception, return an error message in JSON format with HTTP status code 400
            return jsonify({'status': 'error', 'message': str(e)}), 400

# Default route 
@app.route('/')
def index():
    return render_template('index.html')
  
# 
# about page route
# @app.route('/about')
#def about():
#    return render_template('about.html')

# service page route
#@app.route('/service')
#def service():
#    return render_template('service.html')

# recalls_service page route
#@app.route('/recalls_Service')
#def recalls_Service():
#    return render_template('recalls_Service.html')

# benz(recalls_find)page route
#@app.route('/benz')
#def benz():
#    return render_template('benz.html')

if __name__ == '__main__':
    app.run(port=5000) # Runs the Flask application
