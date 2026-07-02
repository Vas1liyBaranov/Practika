from fastapi import FastAPI
from routers import contracts

app = FastAPI(title="Управление договорами аренды", version="1.0.0")

app.include_router(contracts.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API управления договорами"}