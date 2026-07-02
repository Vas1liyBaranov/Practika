<<<<<<< HEAD
from fastapi import FastAPI
from routers import contracts

app = FastAPI(title="Управление договорами аренды", version="1.0.0")

app.include_router(contracts.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API управления договорами"}
=======
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Управление договорами аренды",
    description="API для управления договорами аренды торгового центра", version="1.0.0")

rooms_db = [
    {"id": 1, "number": 101, "floor": 1, "area": 53, "status": "свободно", "rent_cost": 60000},
    {"id": 2, "number": 102, "floor": 1, "area": 79, "status": "занято", "rent_cost": 90000},
    {"id": 3, "number": 201, "floor": 2, "area": 103, "status": "свободно", "rent_cost": 120000},
    {"id": 4, "number": 202, "floor": 2, "area": 124, "status": "ремонт", "rent_cost": 0},
    {"id": 5, "number": 301, "floor": 3, "area": 240, "status": "свободно", "rent_cost": 240000},
]
next_id = 6 

class ContractBase(BaseModel):
    """Базовая модель договора (для создания)"""
    FIO: str
    number_room: int
    area: float
    money: float
    start_date: str
    end_date: str

class ContractCreate(ContractBase): """Модель для создания договора"""
    pass

class ContractResponse(ContractBase): """Модель для ответа (с ID)"""
    id: int

@app.get("/")
def read_root():
    return { "status": "ok", "message": "Добро пожаловать в API управления договорами аренды!",
        "endpoints": {"GET /contracts": "Получить список всех договоров",
            "GET /contracts/{id}": "Получить договор по ID", "POST /contracts": "Создать новый договор"}}

@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Привет, {name}!"}

@app.get("/contracts", response_model=List[ContractResponse])
def get_all_contracts(): """Получить список всех договоров"""
    return contracts_db

@app.get("/contracts", response_model=List[ContractResponse])
def get_all_contracts():
    return contracts_db

@app.get("/contracts/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: int):
    for contract in contracts_db:
        if contract["id"] == contract_id:
            return contract
    raise HTTPException(status_code=404, detail="Договор не найден")

@app.delete("/contracts/{contract_id}")
def delete_contract(contract_id: int):
    for i, contract in enumerate(contracts_db):
        if contract["id"] == contract_id:
            deleted = contracts_db.pop(i)
            return {"message": "Удалено", "deleted": deleted}
    raise HTTPException(status_code=404, detail="Договор не найден")

@app.get("/contracts/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: int): """Получить договор по ID"""
    for contract in contracts_db:
        if contract["id"] == contract_id:
            return contract
    raise HTTPException(status_code=404, detail=f"Договор с ID {contract_id} не найден")

@app.post("/contracts", response_model=ContractResponse, status_code=201)
def create_contract(contract: ContractCreate):
    """Создать новый договор"""
    global next_id
    
    for existing in contracts_db:
        if existing["number_room"] == contract.number_room:
            raise HTTPException(status_code=400, detail=f"Помещение №{contract.number_room} уже занято")
    
    # Создать новый договор
    new_contract = contract.dict()
    new_contract["id"] = next_id
    contracts_db.append(new_contract)
    next_id += 1
    return new_contract

@app.delete("/contracts/{contract_id}")
def delete_contract(contract_id: int): """Удалить договор по ID"""
    global contracts_db
    
    for i, contract in enumerate(contracts_db):
        if contract["id"] == contract_id:
            deleted = contracts_db.pop(i)
            return {"message": f"Договор №{contract_id} удалён", "deleted": deleted}
    
    raise HTTPException(status_code=404, detail=f"Договор с ID {contract_id} не найден")
>>>>>>> d124b9b98a1b25aaaaeb43e2ea259f83c5ebe6fd
