from flask import Flask, jsonify
import random
app = Flask(__name__)
QUOTES = [
  "Kubernetes is the new Linux for the cloud.",
  "Simplicity is prerequisite for reliability.",
  "Move fast; break _nodes_."
]
@app.route("/api/quote")
def quote(): 
    return jsonify({"quote": random.choice(QUOTES)}) 