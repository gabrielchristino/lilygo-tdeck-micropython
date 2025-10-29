"""
WiFi Status App

Verifica o status da conexão e, se desconectado, tenta se conectar
automaticamente às redes salvas.
"""

import time
import network
import ntptime
import st7789py as st7789
from romfonts import vga1_8x8 as font

# --- Constantes ---
BG_COLOR = st7789.color565(10, 20, 40)
TEXT_COLOR = st7789.WHITE
SUCCESS_COLOR = st7789.GREEN
ERROR_COLOR = st7789.RED

# Caminho para o arquivo de senhas criado pelo app wifi_connect
KNOWN_NETWORKS_FILE = '/sd/app/wifi_connect/known_networks.txt'

class App:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.sound = sound
        self.wlan = network.WLAN(network.STA_IF)

    def draw_header(self, text):
        self.display.fill(BG_COLOR)
        self.display.text(font, text, 10, 10, TEXT_COLOR, BG_COLOR)

    def show_message(self, title, message, color):
        self.draw_header(title)
        self.display.text(font, message, 10, 60, color, BG_COLOR)
        time.sleep(3)

    def _sync_time(self):
        """Tenta sincronizar o RTC via NTP e exibe o status."""
        # Limpa a área de mensagens e exibe o status
        self.display.fill_rect(0, 80, self.display.width, 40, BG_COLOR)
        self.display.text(font, "Sincronizando hora...", 10, 80, TEXT_COLOR, BG_COLOR) # type: ignore
        try:
            # ntptime.settime() pode levar alguns segundos e levanta uma exceção em caso de falha
            ntptime.settime()
            self.display.text(font, "Hora atualizada com sucesso!", 10, 100, SUCCESS_COLOR, BG_COLOR) # type: ignore
        except (OSError, AttributeError): # OSError para falha de rede, AttributeError se ntptime não estiver pronto
            self.display.text(font, "Falha ao sincronizar hora.", 10, 100, ERROR_COLOR, BG_COLOR) # type: ignore
        time.sleep(2) # Pausa para o usuário ler a mensagem

    def load_known_networks(self):
        """Carrega redes conhecidas do arquivo de texto."""
        known_networks = {}
        try:
            with open(KNOWN_NETWORKS_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        ssid, password = line.split(':', 1)
                        known_networks[ssid] = password
        except OSError:
            # Arquivo não existe, o que é normal
            pass
        return known_networks

    def run(self):
        # Ativa o Wi-Fi para todas as operações
        self.wlan.active(True)
        time.sleep_ms(200) # Pausa para o hardware inicializar
        
        # 1. Verifica se já está conectado
        if self.wlan.isconnected():
            ssid = self.wlan.config('ssid')
            ip = self.wlan.ifconfig()[0]
            self.draw_header("WiFi Status")
            self.display.text(font, f"Conectado a: {ssid}", 10, 40, SUCCESS_COLOR, BG_COLOR)
            self.display.text(font, f"IP: {ip}", 10, 60, SUCCESS_COLOR, BG_COLOR)
            self._sync_time() # Sincroniza a hora
            # Mantém o WiFi ligado e sai
            return

        # 2. Se não estiver conectado, tenta se conectar às redes salvas
        self.draw_header("Auto-Conexao WiFi")
        known_networks = self.load_known_networks()

        if not known_networks:
            self.show_message("Auto-Conexao", "Nenhuma rede salva.", TEXT_COLOR)
            self.wlan.active(False) # Desliga o WiFi se não há o que fazer
            return

        for ssid, password in known_networks.items():
            self.display.text(font, f"Tentando: {ssid}", 10, 40, TEXT_COLOR, BG_COLOR)
            self.wlan.connect(ssid, password)
            
            # Tenta por 7 segundos
            for _ in range(7):
                if self.wlan.isconnected():
                    break
                time.sleep(1)
            
            if self.wlan.isconnected():
                break # Sai do loop principal se conectou

        # 3. Exibe o resultado final
        if self.wlan.isconnected():
            ip = self.wlan.ifconfig()[0]
            self.draw_header("Conectado!")
            self.display.text(font, f"IP: {ip}", 10, 60, SUCCESS_COLOR, BG_COLOR)
            self._sync_time() # Sincroniza a hora
        else:
            self.show_message("Falha!", "Nao conectou a nenhuma rede.", ERROR_COLOR)
            self.wlan.active(False) # Desliga o WiFi se falhou

# --- Ponto de Entrada do App ---
try: # type: ignore
    app = App(display, touch, trackball, i2c, sound)
    app.run()
except Exception as e:
    print(f"!!! ERRO ao executar WiFi Status App: {e}")
    _display = globals().get('display')
    if _display:
        _display.fill(st7789.RED)
        _display.text(font, "ERRO NO APP", 10, 10, st7789.WHITE, st7789.RED)
        _display.text(font, str(e)[:35], 10, 30, st7789.WHITE, st7789.RED)
        time.sleep(5)