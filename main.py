import os
import cv2
import time
import torch
from dotenv import load_dotenv
from ultralytics import YOLO

# Importa os serviços que nós criamos separadamente
from services.arduino_service import ArduinoService
from services.api_service import ApiService

# Corrige a validação de segurança do PyTorch
torch.serialization.add_safe_globals([
    'ultralytics.nn.tasks.DetectionModel', 'ultralytics.nn.modules.block.C2f',
    'ultralytics.nn.modules.conv.Conv', 'ultralytics.nn.modules.block.DFL',
    'ultralytics.nn.modules.head.Detect', 'ultralytics.nn.modules.conv.Concat',
    'torch.nn.modules.container.Sequential', 'torch.nn.modules.container.ModuleList',
    'torch.nn.modules.conv.Conv2d', 'torch.nn.modules.batchnorm.BatchNorm2d',
    'torch.nn.modules.activation.SiLU', 'torch.nn.modules.pooling.MaxPool2d',
    'ultralytics.nn.modules.block.Bottleneck', 'ultralytics.nn.modules.block.SPPF'
])

load_dotenv()

# Inicializa as configurações
try:
    IRIUN_INDEX = int(os.getenv("IRIUN_INDEX", 1))
except ValueError:
    IRIUN_INDEX = 1

# Instancia os serviços passando as variáveis do .env
arduino_service = ArduinoService(port=os.getenv("SERIAL_PORT"), baud_rate=9600)
api_service = ApiService(url=os.getenv("API_URL"))

# Inicializa IA e Câmera
model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(IRIUN_INDEX)

if not cap.isOpened() and IRIUN_INDEX != 0:
    cap = cv2.VideoCapture(0)

print("[INFO] Sistema FlowSense iniciado. Pressione 'q' para sair.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        time.sleep(1)
        cap = cv2.VideoCapture(IRIUN_INDEX)
        continue

    # Detecta pessoas na tela
    results = model.predict(frame, conf=0.4, classes=[0], verbose=False)

    pessoas_na_tela = 0
    if results[0].boxes is not None:
        pessoas_na_tela = len(results[0].boxes)
        boxes = results[0].boxes.xyxy.cpu().numpy()

        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, "Pessoa Detectada", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # Chamada dos serviços isolados (eles controlam internamente se precisam enviar ou não)
    arduino_service.atualizar_leds(pessoas_na_tela, total_leds=9)
    api_service.notificar_aplicativo(pessoas_na_tela)

    # HUD Visual no PC
    status_texto = f"PRESENCA ({pessoas_na_tela})" if pessoas_na_tela > 0 else "AMBIENTE VAZIO"
    status_cor = (0, 0, 255) if pessoas_na_tela > 0 else (0, 255, 0)
    cv2.rectangle(frame, (5, 5), (280, 50), (0, 0, 0), -1)
    cv2.putText(frame, f"Status: {status_texto}", (15, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_cor, 2)

    cv2.imshow("Controle de Presenca - FlowSense", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Finalização limpa usando os métodos de encerramento
cap.release()
cv2.destroyAllWindows()
arduino_service.fechar()
print("[INFO] Aplicação encerrada com sucesso.")