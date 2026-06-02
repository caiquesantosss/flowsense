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
            print("[AVISO] Porta serial não configurada no arquivo .env. Executando sem Arduino.")
            return

        try:
            self.arduino = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=1
            )

            # Aguarda o reset automático do Arduino após abrir a serial
            time.sleep(2)

            print(f"[INFO] Conectado ao Arduino com sucesso na porta {self.port}")

            self.atualizar_leds(0)

        except Exception as e:
            print(f"[AVISO] Não foi possível conectar ao Arduino na porta {self.port}: {e}")
            self.arduino = None

    def atualizar_leds(self, quantidade_pessoas, total_leds=9):

        if not self.arduino:
            return

        # Mantém o valor dentro dos limites válidos
        leds_para_acender = min(
            max(0, quantidade_pessoas),
            total_leds
        )

        if leds_para_acender == self.ultimo_leds_enviado:
            return

        try:
            # envia um único byte contendo o valor numérico.
            self.arduino.write(bytes([leds_para_acender]))

            self.ultimo_leds_enviado = leds_para_acender

            print(
                f"[ARDUINO] Comando enviado com sucesso: "
                f"{leds_para_acender} LED(s) ativo(s)."
            )

        except Exception as e:
            print(
                f"[ARDUINO ERRO] Falha ao transmitir dados pela serial: {e}"
            )

    def fechar(self):
        if self.arduino:
            try:
                self.arduino.close()
                print("[ARDUINO] Conexão serial encerrada.")
            except Exception as e:
                print(f"[ARDUINO ERRO] Falha ao encerrar conexão: {e}")