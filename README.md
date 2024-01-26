# Distributed-Computing

## About
- This project is a distributed computing system that allows users to run computationally intensive tasks on a network of computers.
- The system is composed of a main server, a commander server, a commander website, and worker nodes.
- The main server is responsible for managing the network of worker nodes and assigning tasks to them.
- The commander server is responsible for managing the commander website and communicating with the main server.
- The commander website is a web interface that allows users to submit tasks to the system and monitor their progress.
- Worker nodes are responsible for running tasks and reporting their progress to the main server.

## How to run locally 

### Main server
- `cd server`
- `python3 server.py`

### Commander server
- `cd web/backend`
- `python3 app.py`

### Commander website
- `cd web/client`
- `npm start`

### Worker nodes
- `cd client`
- `python3 worker.py`