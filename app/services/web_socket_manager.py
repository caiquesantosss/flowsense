from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
        print(f"[WS MANAGER] Celular conectado! Total de conexões ativas: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[WS MANAGER] Celular desconectado. Conexões restantes: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        print(f"[WS BROADCAST] Tentando enviar para {len(self.active_connections)} aparelhos. Dados: {message}")
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WS BROADCAST ERRO] Falha ao enviar para um cliente: {e}")
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

# Garante a instância única (Singleton)
ws_manager = WebSocketManager()