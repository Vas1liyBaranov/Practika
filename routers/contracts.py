from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel, Field

router = APIRouter(prefix="/contracts", tags=["Договоры"])

contracts_db = [
    {"id": 1, "FIO": "Иванов Иван", "number_room": 101, "area": 51, "money": 60000, "start_date": "2026-01-01", "end_date": "2026-12-31"},
    {"id": 2, "FIO": "Петров Петр", "number_room": 102, "area": 72, "money": 90000, "start_date": "2026-02-01", "end_date": "2026-07-31"},
    {"id": 3, "FIO": "Сидорова Анна", "number_room": 201, "area": 103, "money": 120000, "start_date": "2026-03-01", "end_date": "2027-02-28"},
    {"id": 4, "FIO": "Козлов Дмитрий", "number_room": 202, "area": 121, "money": 144000, "start_date": "2026-04-01", "end_date": "2026-09-30"},
    {"id": 5, "FIO": "Морозова Елена", "number_room": 301, "area": 89, "money": 96000, "start_date": "2026-05-01", "end_date": "2027-04-30"},
]

next_id = 6

class ContractIn(BaseModel):
    FIO: str = Field(min_length=2, max_length=100)
    number_room: int = Field(gt=0)
    area: float = Field(gt=0)
    money: float = Field(gt=0)
    start_date: str
    end_date: str

class ContractOut(BaseModel):
    id: int
    FIO: str
    number_room: int
    area: float
    money: float
    start_date: str
    end_date: str

def pagination(limit: int = 10, offset: int = 0):
    return {"limit": limit, "offset": offset}

@router.get("/", response_model=List[ContractOut])
def get_all_contracts(p: dict = Depends(pagination)):
    start = p["offset"]
    end = start + p["limit"]
    return contracts_db[start:end]

@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: int):
    for contract in contracts_db:
        if contract["id"] == contract_id:
            return contract
    raise HTTPException(status_code=404, detail=f"Договор с ID {contract_id} не найден")

@router.post("/", response_model=ContractOut, status_code=201)
def create_contract(contract: ContractIn):
    global next_id
    for existing in contracts_db:
        if existing["number_room"] == contract.number_room:
            raise HTTPException(status_code=400, detail=f"Помещение №{contract.number_room} уже занято")
    new_contract = contract.dict()
    new_contract["id"] = next_id
    contracts_db.append(new_contract)
    next_id += 1
    return new_contract

@router.delete("/{contract_id}")
def delete_contract(contract_id: int):
    global contracts_db
    for i, contract in enumerate(contracts_db):
        if contract["id"] == contract_id:
            deleted = contracts_db.pop(i)
            return {"message": f"Договор №{contract_id} удалён", "deleted": deleted}
    raise HTTPException(status_code=404, detail=f"Договор с ID {contract_id} не найден")