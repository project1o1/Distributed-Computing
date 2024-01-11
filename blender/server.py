import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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

connected_workers = []

@app.post("/connect")
async def connect(port: int, ip: str):
    connected_workers.append({
        "port": port,
        "ip": ip
    })
    print(connected_workers)
    return {"message": "Connected"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)