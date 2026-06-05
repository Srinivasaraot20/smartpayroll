
from flask import Flask
app = Flask(__name__)

# Import routes after Flask app initialization
from app import *  # This imports all routes and configurations

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
