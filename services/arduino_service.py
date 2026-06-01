import serial
import time

class ArduinoService:
    def __init__(self, port, baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.arduino = None
        self.ultimo_leds_enviado = -1
        self._conectar()

    def _conectar(self):
        if not self.port:
            print("[AVISO] Porta serial não configurada. Executando sem Arduino.")
            return
        try:
            self.arduino = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Aguarda o Arduino resetar
            print(f"[INFO] Conectado ao Arduino na porta {self.port}")
            # Inicializa apagado
            self.atualizar_leds(0)
        except Exception as e:
            print(f"[AVISO] Não foi possível conectar ao Arduino: {e}")
            self.arduino = None

    def atualizar_leds(self, quantidade_pessoas, total_leds=9):
        """Envia a quantidade de LEDs que devem acender para o Arduino."""
        if not self.arduino:
            return

        leds_para_acender = min(quantidade_pessoas, total_leds)
        
        # Só envia se o valor mudou para não inundar a serial
        if leds_para_acender != self.ultimo_leds_enviado:
            try:
                self.arduino.write(bytes([leds_para_acender]))
                self.ultimo_leds_enviado = leds_para_acender
            except Exception as e:
                print(f"[ARDUINO ERRO] Falha ao enviar dados: {e}")

    def fechar(self):
        if self.arduino:
            self.arduino.close()