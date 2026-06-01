import requests
import time
import threading  # Biblioteca nativa para criar processos em segundo plano

class ApiService:
    def __init__(self, url):
        self.url = url
        self.ultima_contagem_enviada = -1

    def _executar_envio_paralelo(self, payload):
        """Função interna que roda em segundo plano para fazer o POST sem travar o OpenCV."""
        try:
            # Como roda em paralelo, o timeout pode ser até maior se necessário, sem afetar o vídeo
            response = requests.post(self.url, json=payload, timeout=3.0)
            print(f"[API APP] Notificado com sucesso! Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[API APP ERRO] Falha ao enviar em segundo plano: {e}")

    def notificar_aplicativo(self, quantidade_atual):
        """Dispara o envio de informações criando uma Thread paralela assíncrona."""
        if not self.url:
            return
        if quantidade_atual == self.ultima_contagem_enviada:
            return
        
        self.ultima_contagem_enviada = quantidade_atual

        status = "PRESENCA" if quantidade_atual > 0 else "VAZIO"
        payload = {
            "quantidade_atual": quantidade_atual,
            "status_ambiente": status,
            "timestamp": int(time.time())
        }

        print(f"[API APP] Criando tarefa de segundo plano para {quantidade_atual} pessoas...")
        
        thread_api = threading.Thread(target=self._executar_envio_paralelo, args=(payload,))
        
        # Define como daemon para que ela feche automaticamente se você fechar o programa principal
        thread_api.daemon = True
        
        # Dispara a thread e libera o main.py INSTANTANEAMENTE
        thread_api.start()