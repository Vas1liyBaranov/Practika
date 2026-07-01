from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Модель для создания договора (ОПРЕДЕЛЯЕМ ДО ИСПОЛЬЗОВАНИЯ!)
class ContractCreate(BaseModel):
    tenant_name: str
    room_number: int
    area: float
    monthly_rent: float
    start_date: str
    end_date: str


@app.get("/")
def read_root():
    return {"status": "ok"}


@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Привет, {name}"}


@app.post("/contracts/")
def create_contract(contract: ContractCreate):
    return {
        "message": f"Договор для {contract.tenant_name} создан!",
        "room": contract.room_number,
        "area": contract.area,
        "monthly_rent": contract.monthly_rent,
        "period": f"{contract.start_date} — {contract.end_date}"
    }