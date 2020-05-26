# Example Server
This is a server that accepts a single example from a Flipper user and tries to generalize it to a definition.
The routes can be found [here](../flipper-explanations/flipper-examples-backend.postman_collection.json)

## Installation
 - create a virtual environment for python3
 - run `pip install -r requirements.txt`

## Running
In order to run the server, run `export FLASK_APP=flask-routes.py` and then `flask run`. 
The server will run on the port 5000