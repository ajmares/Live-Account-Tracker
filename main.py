print("=== main.py is running! ===")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import subprocess
import logging

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

try:
    print("Registering /revenue endpoint")
    @app.get("/revenue")
    def get_revenue():
        try:
            with open(REVENUE_DATA_PATH, "r") as f:
                data = json.load(f)
            return {"data": data}
        except Exception as e:
            return {"error": str(e)}
except Exception as e:
    print("Error registering /revenue:", e)

try:
    print("Registering /last_updated endpoint")
    @app.get("/last_updated")
    def get_last_updated():
        try:
            with open("last_updated.txt", "r") as f:
                ts = f.read().strip()
            return {"last_updated": ts}
        except Exception as e:
            return {"error": str(e)}
except Exception as e:
    print("Error registering /last_updated:", e)

try:
    print("Registering /trigger-update endpoint")
    @app.post("/trigger-update")
    def trigger_update():
        logging.warning("/trigger-update endpoint was called")
        try:
            result = subprocess.run(["python3", "fetch_revenue_data.py"], check=True, capture_output=True, text=True)
            return JSONResponse(content={"status": "success", "message": "Data updated successfully", "output": result.stdout})
        except subprocess.CalledProcessError as e:
            return JSONResponse(content={"status": "error", "message": str(e), "output": e.output}, status_code=500)
        except Exception as e:
            return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
except Exception as e:
    print("Error registering /trigger-update:", e) 