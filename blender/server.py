import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import nanoid
import requests


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

connected_workers = {}

class Connection(BaseModel):
    port: int
    ip: str

@app.post("/connect")
async def connect(connection: Connection):
    # connected_workers.append({
    #     "port": connection.port,
    #     "ip": connection.ip
    # })

    id = nanoid.generate()

    connected_workers[id] = {
        "port": connection.port,
        "ip": connection.ip
    }
    print(connected_workers)
    return {"message": "Connected", "id": id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)