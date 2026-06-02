import os
import cv2
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from ultralytics import YOLO
import uvicorn

# Importações da arquitetura FlowSense
from app.config.database import engine, Base
from app.controllers.ocupacao_controller import router as ocupacao_router
from app.services.web_socket_manager import ws_manager
from app.services.arduino_service import ArduinoService

load_dotenv()

# Objeto global vazio para referenciamento seguro dentro da thread de execução
arduino_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global arduino_service
    print("\n[BANCO] Verificando e criando tabelas no SQLite...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    print("[SISTEMA] Conectando ao barramento de hardware...")
    arduino_service = ArduinoService(port=os.getenv("SERIAL_PORT"), baud_rate=9600)
    
    print("[SISTEMA] Inicializando linha de processamento de Visão Computacional...")
    asyncio.create_task(rodar_visao_computacional_async())
    
    yield
    print("[SISTEMA] Desligando servidores e liberando hardwares...")
    if arduino_service:
        arduino_service.fechar()

app = FastAPI(title="FlowSense Core API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ocupacao_router)

# Suprime os avisos de segurança de serialização do PyTorch
import torch
torch.serialization.add_safe_globals([
    'ultralytics.nn.tasks.DetectionModel', 'ultralytics.nn.modules.block.C2f',
    'ultralytics.nn.modules.conv.Conv', 'ultralytics.nn.modules.block.DFL',
    'ultralytics.nn.modules.head.Detect', 'ultralytics.nn.modules.conv.Concat',
    'torch.nn.modules.container.Sequential', 'torch.nn.modules.container.ModuleList',
    'torch.nn.modules.conv.Conv2d', 'torch.nn.modules.batchnorm.BatchNorm2d',
    'torch.nn.modules.activation.SiLU', 'torch.nn.modules.pooling.MaxPool2d',
    'ultralytics.nn.modules.block.Bottleneck', 'ultralytics.nn.modules.block.SPPF'
])

# ROTA WEBSOCKET RESTAURADA PARA O PADRÃO SEGURO
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Passamos o controle direto para o manager fazer o handshake limpo
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

async def rodar_visao_computacional_async():
    global arduino_service
    IRIUN_INDEX = int(os.getenv("IRIUN_INDEX", 0))

    print("[IA] Carregando pesos do modelo YOLOv8...")
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(IRIUN_INDEX, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print(f"[ERRO] Não foi possível abrir o dispositivo de captura no índice {IRIUN_INDEX}.")
        return

    print("[IA] Câmera ativada com sucesso. Monitoramento em tempo real iniciado...")

    while True:
        ret, frame = cap.read()
        if not ret:
            await asyncio.sleep(0.03)
            continue

        results = model(frame, conf=0.4, classes=[0], verbose=False)
        quantidade_atual = len(results[0].boxes)
        status_ambiente = "PRESENCA" if quantidade_atual > 0 else "VAZIO"

        print(f"[IA PROCESSAMENTO] Pessoas: {quantidade_atual} | Status: {status_ambiente}")

        # 1. Envia os dados para acender os LEDs físicos do Arduino
        if arduino_service and arduino_service.arduino is not None:
            arduino_service.atualizar_leds(quantidade_atual)

        # 2. Transmite os dados em tempo real para o celular via WebSocket
        await ws_manager.broadcast({
            "quantidade_atual": quantidade_atual,
            "status_ambiente": status_ambiente,
            "timestamp": int(time.time())
        })

        # Renderização gráfica do OpenCV
        annotated_frame = results[0].plot()
        cv2.imshow("FlowSense - Monitoramento IA", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        await asyncio.sleep(0.001)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)