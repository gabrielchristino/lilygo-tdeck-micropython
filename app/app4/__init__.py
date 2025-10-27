"""Exemplo de Aplicação: Entrada de Teclado"""

import time
import st7789py as st7789
from romfonts import vga1_8x8 as font
from lib.ui_manager import UIManager
from lib.keyboard import get_key # Importa a função get_key

# Os objetos de hardware (display, touch, trackball, i2c, sound) são injetados como globais.

print("Executando Exemplo de Teclado Input")

# --- Configuração da UI ---
BG_COLOR = st7789.color565(30, 30, 30) # Fundo cinza escuro
TEXT_COLOR = st7789.WHITE
INPUT_BG_COLOR = st7789.color565(50, 50, 50) # Fundo do input um pouco mais claro

display.fill(BG_COLOR)
display.text(font, "TECLADO INPUT", 60, 10, TEXT_COLOR, BG_COLOR)
display.text(font, "Digite algo:", 10, 50, TEXT_COLOR, BG_COLOR)

# Inicializa o UIManager com os objetos de hardware injetados
# Agora o UIManager recebe 'trackball' e 'sound' como argumentos.
ui_manager = UIManager(display, touch, i2c, font, trackball, sound)

# Adiciona um campo de texto
text_input = ui_manager.add_text_input(
    x=10, y=70, w=300, h=30,
    placeholder="Seu texto aqui...",
    bg_color=INPUT_BG_COLOR,
    text_color=TEXT_COLOR
)

# Define o campo de texto como focado inicialmente
ui_manager.focused_input = text_input
text_input.focused = True
text_input.draw(display) # Desenha com o foco

# --- Loop Principal do Aplicativo ---
app_running = True
while app_running:
    # Processa eventos de toque para focar campos
    ui_manager.handle_touch()

    # Processa eventos do trackball para navegação e confirmação.
    # Se handle_trackball retornar True, significa que um clique de confirmação
    # foi processado no campo focado, e o app deve sair.
    if ui_manager.handle_trackball():
        app_running = False # Sair do app após confirmação

    # Processa entrada do teclado
    # A função get_key é passada para o UIManager para que ele possa ler as teclas.
    ui_manager.handle_keyboard(get_key)

    time.sleep_ms(50)

# Exibe o valor final antes de sair
display.fill(BG_COLOR)
display.text(font, "App Encerrado!", 60, 60, TEXT_COLOR, BG_COLOR)
display.text(font, f"Valor final: {text_input.value}", 10, 100, TEXT_COLOR, BG_COLOR)
time.sleep(3)
