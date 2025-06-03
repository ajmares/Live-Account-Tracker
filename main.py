from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REVENUE_DATA_PATH = os.getenv("REVENUE_DATA_PATH", "revenue_data.json")

@app.get("/revenue")
def get_revenue():
    try:
        with open(REVENUE_DATA_PATH, "r") as f:
            data = json.load(f)
        return {"data": data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/last_updated")
def get_last_updated():
    try:
        with open("last_updated.txt", "r") as f:
            ts = f.read().strip()
        return {"last_updated": ts}
    except Exception as e:
        return {"error": str(e)} 