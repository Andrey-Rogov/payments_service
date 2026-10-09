from fastapi import FastAPI
from api import payments_router

app = FastAPI()
app.include_router(payments_router, prefix="/api/v1")
