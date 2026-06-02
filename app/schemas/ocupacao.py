from pydantic import BaseModel
from datetime import datetime

class OcupacaoCreate(BaseModel):
    quantidade_atual: int
    status_ambiente: str

class OcupacaoResponse(BaseModel):
    id: str
    quantidade_atual: int
    status_ambiente: str
    timestamp: datetime

    class Config:
        from_attributes = True