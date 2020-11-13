# Interactive Synthesis
This is a server that accepts a single example from a LTLTalk user
together with the corresponding natural language definitions, 
and tries to generalize it to a definition.


## Setting up the environment
 - create a virtual environment for python3 (for example, using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/))
 - run `pip install -r requirements.txt`
 - run `export FLASK_APP=flask-routes.py` (or add it to the `.bashrc` file)

## Running
-  `flask run`. 
(The server will run on the port 5000 by default)

## Interacting with the whole system

## Setup
Install [frontend](https://github.com/mpi-sws-rse/ltltalk-frontend), 
[semantic parser](https://github.com/mpi-sws-rse/ltltalk-backend), 
and [interactive synthesis engine](https://github.com/mpi-sws-rse/ltltalk-interactive-synthesis) locally. To install each part, please follow the instructions in the corresponding repositories.





## Basic system functionality


In order to have a view of the overall system (as shown in Fig. 2 of the paper), do the following:
Terminal 1: 
 - navigate to the ltltalk-backend directory and run `./interactive/run @mode=ltltalk`

Terminal 2: 
 - navigate to interactive-synthesis directory 
 - run `workon ltlTalk' (to use the correct python virtual environment)
 - run `flask run'

Terminal 3:
 - navigate to the frontend directory
 - enter folder `voxelurn`
 - run `yarn start`

Terminal 1 runs the naturalization server (described in Section 5 of the paper). Terminal 2 runs the interactive synthesis server (described in Section 4 of the paper). Finally, Terminal 3 runs the frontend. Upon running `yarn start`, a firefox window should open. If this does not happen, visit `localhost:3000` in a browser.

Navigate to the Play tab of the frontend. (For the moment, disregard other tabs as they are not completely up to date.) To test the system, try the example from the paper:
 - write `take one red item from 7,4`
 - the robot will not know what is meant by that and will ask for clarification: do it using arrows and pressing P for picking (these instructions will be provided in the frontend as well)
 - the system will show a couple of demonstrations for which you have to judge whether or not they fit to the intended command. (This process is not deterministic so the number of questions can vary.)
 - once the process is finished, try `take every triangle item from 10, 8` . Now, the system should be able to parse it and execute the action.


