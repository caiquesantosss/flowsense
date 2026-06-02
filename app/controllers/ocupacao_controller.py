from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config.database import get_db
from app.models.ocupacao import OcupacaoModel
from app.schemas.ocupacao import OcupacaoCreate, OcupacaoResponse
from app.services.web_socket_manager import ws_manager
import time

router = APIRouter(prefix="/api/presenca", tags=["Ocupação"])

@router.post("/", response_model=OcupacaoResponse, status_code=201)
async def registrar_evento(payload: OcupacaoCreate, db: AsyncSession = Depends(get_db)):
    """Rota que sua Thread local do OpenCV vai acionar para atualizar o ecossistema"""
    try:
        novo_registro = OcupacaoModel(
            quantidade_atual=payload.quantidade_atual,
            status_ambiente=payload.status_ambiente
        )
        db.add(novo_registro)
        await db.flush() # Gera o ID e o timestamp
        
        # 2. Transmite via WebSocket para o React Native em tempo real
        await ws_manager.broadcast({
            "quantidade_atual": novo_registro.quantidade_atual,
            "status_ambiente": novo_registro.status_ambiente,
            "timestamp": int(time.time())
        })
        
        return novo_registro
    except Exception as e:
        print(f"[ERRO CONTROLLER]: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao registrar ocupação.")

@router.get("/historico", response_model=list[OcupacaoResponse])
async def buscar_historico(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OcupacaoModel).order_by(OcupacaoModel.timestamp.desc()).limit(100))
    return result.scalars().all()