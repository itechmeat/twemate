from fastapi import FastAPI
from app.api.routes import setup_routes

app = FastAPI(title="TwiMate API")

setup_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4750) 