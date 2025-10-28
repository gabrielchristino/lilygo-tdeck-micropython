"""
WiFi Manager App

Escaneia, conecta e salva redes WiFi.
"""

import time
import network
import os
import st7789py as st7789
from romfonts import vga1_8x8 as font
from lib.ui_manager import UIManager
from lib.keyboard import get_key

# --- Constantes ---
BG_COLOR = st7789.color565(10, 20, 40)
TEXT_COLOR = st7789.WHITE
HIGHLIGHT_COLOR = st7789.CYAN
INPUT_BG_COLOR = st7789.color565(20, 40, 60)
SUCCESS_COLOR = st7789.GREEN
ERROR_COLOR = st7789.RED

KNOWN_NETWORKS_FILE = '/sd/app/wifi_manager/known_networks.txt'

# --- Hardware Injetado (vem do app_runner) ---
# display, touch, i2c, trackball, sound

# --- Funções Auxiliares ---

def draw_header(text):
    """Desenha um cabeçalho padronizado."""
    display.fill(BG_COLOR)
    display.text(font, text, 10, 10, TEXT_COLOR, BG_COLOR)

def show_message(title, message, color):
    """Exibe uma mensagem na tela por alguns segundos."""
    draw_header(title)
    display.text(font, message, 10, 60, color, BG_COLOR)
    time.sleep(3)

def load_known_networks():
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
        # Arquivo não existe, o que é normal na primeira execução
        pass
    return known_networks

def save_network(ssid, password):
    """Salva uma nova rede no arquivo."""
    try:
        with open(KNOWN_NETWORKS_FILE, 'a') as f:
            f.write(f"{ssid}:{password}\n")
        print(f"Rede '{ssid}' salva.")
    except Exception as e:
        print(f"Erro ao salvar rede: {e}")


# --- Lógica Principal do App ---

print("Executando WiFi Manager")

# 1. Inicializa WiFi e escaneia redes
draw_header("WiFi Manager")
display.text(font, "Escaneando redes...", 10, 50, TEXT_COLOR, BG_COLOR)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

try:
    networks = wlan.scan()
except Exception as e:
    show_message("Erro de WiFi", "Falha ao escanear.", ERROR_COLOR)
    networks = []

if not networks:
    if not wlan.isconnected():
        show_message("WiFi Manager", "Nenhuma rede encontrada.", TEXT_COLOR)
else:
    # Ordena as redes por força do sinal (RSSI), do mais forte para o mais fraco
    networks.sort(key=lambda x: x[3], reverse=True)
    ssids = [net[0].decode('utf-8') for net in networks]
    
    # 2. Exibe a lista de redes e permite a seleção
    selected_index = 0
    last_selected_index = -1
    app_running = True

    while app_running:
        draw_header("Selecione uma rede:")
        
        # Desenha a lista de SSIDs
        for i, ssid in enumerate(ssids):
            y = 40 + i * 20
            color = HIGHLIGHT_COLOR if i == selected_index else TEXT_COLOR
            display.text(font, f"> {ssid[:25]}", 10, y, color, BG_COLOR)

        # Loop de seleção
        selection_done = False
        while not selection_done:
            direction, click = trackball.get_direction()
            if direction:
                old_index = selected_index
                if direction == 'up':
                    selected_index = max(0, selected_index - 1)
                elif direction == 'down':
                    selected_index = min(len(ssids) - 1, selected_index + 1)
                
                if selected_index != old_index:
                    # Redesenha apenas os itens que mudaram
                    display.text(font, f"> {ssids[old_index][:25]}", 10, 40 + old_index * 20, TEXT_COLOR, BG_COLOR)
                    display.text(font, f"> {ssids[selected_index][:25]}", 10, 40 + selected_index * 20, HIGHLIGHT_COLOR, BG_COLOR)
                    sound.play_navigation()

            if click:
                selection_done = True
                app_running = False # Sai do loop principal de seleção
                sound.play_confirm()

            time.sleep_ms(50)

    # 3. Pede a senha e tenta conectar
    selected_ssid = ssids[selected_index]
    known_networks = load_known_networks()
    password = known_networks.get(selected_ssid, "")

    # Configura a UI para entrada de senha
    draw_header(f"Senha para: {selected_ssid[:20]}")
    ui_manager = UIManager(display, touch, i2c, font, trackball, sound)
    
    text_input = ui_manager.add_text_input(
        x=10, y=70, w=300, h=30,
        placeholder="Senha...",
        bg_color=INPUT_BG_COLOR,
        text_color=TEXT_COLOR
    )
    text_input.value = password # Preenche a senha se for conhecida
    ui_manager.focused_input = text_input
    text_input.focused = True
    text_input.draw(display)

    # Loop de entrada de teclado
    password_confirmed = False
    while not password_confirmed:
        ui_manager.handle_touch()
        if ui_manager.handle_trackball(): # Retorna True no clique de confirmação
            password_confirmed = True
        ui_manager.handle_keyboard(get_key)
        time.sleep_ms(50)

    password = text_input.value

    # 4. Tenta conectar
    if password:
        draw_header("Conectando...")
        display.text(font, f"Conectando a {selected_ssid}...", 10, 60, TEXT_COLOR, BG_COLOR)
        
        wlan.connect(selected_ssid, password)
        
        # Aguarda a conexão por até 10 segundos
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            time.sleep(1)
            display.text(font, ".", 10 + (10 - max_wait) * 8, 80, TEXT_COLOR, BG_COLOR)

        # 5. Mostra o resultado
        if wlan.isconnected():
            show_message("Sucesso!", "Conectado a rede!", SUCCESS_COLOR)
            # Salva a rede se for uma nova senha
            if known_networks.get(selected_ssid) != password:
                save_network(selected_ssid, password)
        else:
            show_message("Falha!", "Nao foi possivel conectar.", ERROR_COLOR)
    else:
        show_message("Cancelado", "Conexao sem senha.", TEXT_COLOR)

# 6. Fim do App
print("WiFi Manager encerrado.")
draw_header("WiFi Manager")
display.text(font, "App encerrado.", 10, 60, TEXT_COLOR, BG_COLOR)
time.sleep(2)