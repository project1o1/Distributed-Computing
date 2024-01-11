import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import socket

server = "http://localhost:5000"


app = FastAPI()

# CORS allow all origins
origins = [ "*" ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

@app.get("/")
async def root():
    return {"message": "Hello World"}


def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

def connect():
    response = requests.post(f"{server}/connect", json={
    "port": 8001,
    "ip": get_ip_address()
    })

    print(response.json())


if __name__ == "__main__":
    connect()
    uvicorn.run(app, host="0.0.0.0", port=8001)