"""
WiFi Connect App - VERSÃO FINAL E ROBUSTA

Remove completamente a dependência do módulo 'os' para evitar conflitos.
"""

import time
import network
import st7789py as st7789
from romfonts import vga1_8x8 as font

# --- Constantes ---
BG_COLOR = st7789.color565(10, 20, 40)
TEXT_COLOR = st7789.WHITE
HIGHLIGHT_COLOR = st7789.CYAN
INPUT_BG_COLOR = st7789.color565(20, 40, 60)
SUCCESS_COLOR = st7789.GREEN
ERROR_COLOR = st7789.RED
KBD_I2C_ADDR = 0x55
# Caminho absoluto para o arquivo de senhas, não depende do módulo 'os'.
KNOWN_NETWORKS_FILE = '/sd/app/wifi_connect/known_networks.txt'

class App:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.trackball = trackball
        self.i2c = i2c
        self.sound = sound
        self.wlan = network.WLAN(network.STA_IF)

    def draw_header(self, text):
        self.display.fill(BG_COLOR)
        self.display.text(font, text, 10, 10, TEXT_COLOR, BG_COLOR)

    def show_message(self, title, message, color):
        self.draw_header(title)
        self.display.text(font, message, 10, 60, color, BG_COLOR)
        time.sleep(3)

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
            pass # Arquivo não existe, normal na primeira execução.
        return known_networks

    def save_network(self, ssid, password):
        """Salva uma nova rede no arquivo."""
        try:
            with open(KNOWN_NETWORKS_FILE, 'a') as f:
                f.write(f"{ssid}:{password}\n")
            print(f"Rede '{ssid}' salva.")
        except Exception as e:
            print(f"Erro ao salvar rede: {e}")

    def get_key_simple(self):
        """Lê uma tecla do teclado, sem importar bibliotecas externas."""
        try:
            key = self.i2c.readfrom(KBD_I2C_ADDR, 1)
            if key != b'\x00':
                return key
        except OSError:
            pass
        return None

    def run(self):
        print("Executando WiFi Connect App (Robusto)")

        # --- ETAPA 1: Ligar WiFi e Escanear ---
        self.wlan.active(True)
        self.draw_header("WiFi Connect")
        self.display.text(font, "Escaneando redes...", 10, 50, TEXT_COLOR, BG_COLOR)

        try:
            networks = self.wlan.scan()
        except Exception as e:
            self.show_message("Erro de WiFi", "Falha ao escanear.", ERROR_COLOR)
            networks = []

        # --- ETAPA 2: DESLIGAR o WiFi para a UI ---
        print("Desativando WiFi para a UI...")
        self.wlan.active(False)
        time.sleep_ms(100)
        
        if not networks:
            self.show_message("WiFi Connect", "Nenhuma rede encontrada.", TEXT_COLOR)
            return

        networks.sort(key=lambda x: x[3], reverse=True)
        ssids = [net[0].decode('utf-8') for net in networks]
        
        # --- ETAPA 3: UI de Seleção ---
        selected_ssid = self.select_network_ui(ssids)
        
        # --- ETAPA 4: UI de Senha (Simplificada) ---
        if selected_ssid:
            password = self.get_password_ui_simple(selected_ssid)
            
            # --- ETAPA 5: Conexão ---
            if password is not None:
                self.attempt_connection(selected_ssid, password)

    def get_password_ui_simple(self, ssid):
        """UI de entrada de senha simplificada, sem dependências externas."""
        password = self.load_known_networks().get(ssid, "")
        self.draw_header(f"Senha para: {ssid[:20]}")
        self.display.text(font, "Enter para confirmar", 10, 220, TEXT_COLOR, BG_COLOR)

        while True:
            self.display.fill_rect(10, 80, 220, 20, INPUT_BG_COLOR)
            self.display.rect(10, 80, 220, 20, TEXT_COLOR)
            self.display.text(font, password, 15, 86, TEXT_COLOR, INPUT_BG_COLOR)

            key = self.get_key_simple()
            _, click = self.trackball.get_direction()

            if click or (key and key == b'\r'):
                self.sound.play_confirm()
                return password
            elif key:
                if key == b'\x08': # Backspace
                    password = password[:-1]
                else:
                    try:
                        if len(password) < 25:
                            password += key.decode('utf-8')
                    except UnicodeError:
                        pass
                self.sound.play_keypress()
            time.sleep_ms(20)

    def attempt_connection(self, ssid, password):
        try:
            print("Reativando WiFi para conectar...")
            self.wlan.active(True)
            time.sleep_ms(500)
            self.draw_header("Conectando...")
            self.display.text(font, f"Conectando a {ssid}...", 10, 60, TEXT_COLOR, BG_COLOR)
            self.wlan.connect(ssid, password)
            
            max_wait = 10
            while max_wait > 0:
                if self.wlan.isconnected(): break
                max_wait -= 1
                time.sleep(1)
                self.display.text(font, ".", 10 + (10 - max_wait) * 8, 80, TEXT_COLOR, BG_COLOR)

            if self.wlan.isconnected():
                ip = self.wlan.ifconfig()[0]
                self.show_message("Sucesso!", f"IP: {ip}", SUCCESS_COLOR)
                self.save_network(ssid, password)
            else:
                self.show_message("Falha!", "Nao foi possivel conectar.", ERROR_COLOR)
        finally:
            pass # Mantém o WiFi ligado

    def select_network_ui(self, ssids):
        selected_index = 0
        while True: 
            self.draw_header("Selecione uma rede:")
            for i, ssid in enumerate(ssids):
                y = 40 + i * 20
                color = HIGHLIGHT_COLOR if i == selected_index else TEXT_COLOR
                # Limita a exibição para não sobrepor o botão Sair
                if y < 210:
                    self.display.text(font, f"> {ssid[:25]}", 10, y, color, BG_COLOR)

            # Desenha o botão Sair
            is_exit_focused = (selected_index == len(ssids))
            exit_color = HIGHLIGHT_COLOR if is_exit_focused else TEXT_COLOR
            self.display.text(font, "[ Sair ]", 10, 225, exit_color, BG_COLOR)

            while True:
                direction, click = self.trackball.get_direction()
                key = self.get_key_simple()
                if direction:
                    old_index = selected_index
                    if direction == 'up':
                        selected_index = (selected_index - 1) % (len(ssids) + 1)
                    elif direction == 'down':
                        selected_index = (selected_index + 1) % (len(ssids) + 1)

                    if selected_index != old_index:
                        self.sound.play_navigation()
                        break
                if click or (key and key == b'\r'):
                    if selected_index == len(ssids): # Botão Sair selecionado
                        return None # Retorna None para indicar saída
                    else:
                        self.sound.play_confirm()
                        return ssids[selected_index]
                time.sleep_ms(50)

# --- Ponto de Entrada do App ---
try:
    app = App(display, touch, trackball, i2c, sound)
    app.run()
    print("WiFi Connect App encerrado.")
    app.draw_header("WiFi Connect")
    app.display.text(font, "App encerrado.", 10, 60, TEXT_COLOR, BG_COLOR)
    time.sleep(2)
except Exception as e:
    print(f"!!! ERRO ao instanciar ou rodar a classe App: {e}")
