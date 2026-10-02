from fastapi import FastAPI
from dashboard.routes import router

app = FastAPI(title="Tripline Dashboard")
app.include_router(router)
