"""
Calculator App - Calculadora para T-Deck

Permite realizar cálculos matemáticos usando o teclado físico.
"""

import time
import math
import st7789py as st7789
from romfonts import vga1_8x8 as font

# --- Constantes ---
BG_COLOR = st7789.color565(10, 15, 25)
EXPRESSION_BG_COLOR = st7789.color565(20, 30, 50)
RESULT_BG_COLOR = st7789.color565(30, 45, 70)
TEXT_COLOR = st7789.WHITE
ERROR_COLOR = st7789.RED
KBD_I2C_ADDR = 0x55

class CalculatorApp:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.trackball = trackball
        self.i2c = i2c
        self.sound = sound
        
        # Mapeamento de teclas para caracteres da calculadora
        self.key_map = {
            b'w': '1', b'e': '2', b'r': '3',
            b's': '4', b'd': '5', b'f': '6',
            b'z': '7', b'x': '8', b'c': '9',
            b'q': '0',
            b'a': '*', b'g': '/', b'i': '-', b'o': '+',
            b'm': '.', b'b': '!',
            # 't' é especial para parênteses
        }
        
        # Estado da calculadora
        self.current_expression = ""
        self.result_text = "Resultado..."
        self.parenthesis_open = False # Para alternar '(' e ')'

    def get_key_simple(self):
        """Lê uma tecla do teclado I2C."""
        try:
            key = self.i2c.readfrom(KBD_I2C_ADDR, 1)
            if key != b'\x00': return key
        except OSError: pass
        return None

    def draw_ui(self):
        """Desenha a interface da calculadora."""
        self.display.fill(BG_COLOR)
        
        # Área da Expressão
        self.display.fill_rect(10, 10, 300, 40, EXPRESSION_BG_COLOR)
        self.display.text(font, "Expr:", 15, 15, TEXT_COLOR, EXPRESSION_BG_COLOR)
        # Exibe a expressão da direita para a esquerda se for muito longa
        max_chars_expr = 35
        display_expr = self.current_expression
        if len(display_expr) > max_chars_expr:
            display_expr = "..." + display_expr[-(max_chars_expr-3):]
        self.display.text(font, display_expr, 15, 30, TEXT_COLOR, EXPRESSION_BG_COLOR)

        # Área do Resultado
        self.display.fill_rect(10, 60, 300, 40, RESULT_BG_COLOR)
        self.display.text(font, "Res:", 15, 65, TEXT_COLOR, RESULT_BG_COLOR)
        # Determina a cor do resultado (branco para normal, vermelho para erro)
        res_color = ERROR_COLOR if "Erro" in self.result_text else TEXT_COLOR
        self.display.text(font, self.result_text[:35], 15, 80, res_color, RESULT_BG_COLOR)

        # Instruções
        self.display.text(font, "Enter: Calcular", 10, 120, TEXT_COLOR, BG_COLOR)
        self.display.text(font, "Backspace: Apagar", 10, 135, TEXT_COLOR, BG_COLOR)
        self.display.text(font, "Trackball Click: Limpar Tudo", 10, 150, TEXT_COLOR, BG_COLOR)
        self.display.text(font, "Trackball Direita: Sair", 10, 165, TEXT_COLOR, BG_COLOR)

    def _preprocess_expression(self, expr):
        """Substitui 'n!' por 'math.factorial(n)'."""
        # Esta é uma implementação simples. Para expressões complexas como (5+2)!,
        # seria necessário um parser mais avançado.
        # Funciona bem para casos como "5!", "12!+3", etc.
        parts = expr.split('!')
        processed_expr = ""
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                processed_expr += part
                continue
            
            # Encontra o número antes do '!'
            num_str = ""
            for char in reversed(part):
                if char.isdigit() or char == '.':
                    num_str = char + num_str
                else:
                    break
            
            if num_str:
                # Substitui o número por math.factorial(numero)
                prefix = part[:-len(num_str)]
                processed_expr += f"{prefix}math.factorial({int(num_str)})"
            else:
                # Se não encontrou um número, apenas adiciona o '!' de volta
                processed_expr += part + "!"
        
        return processed_expr

    def run(self):
        """Loop principal do aplicativo."""
        self.draw_ui()

        while True:
            key = self.get_key_simple()
            direction, click = self.trackball.get_direction()

            needs_redraw = False

            if key:
                self.sound.play_keypress()
                needs_redraw = True
                
                if key == b'\r': # Enter: Calcular
                    if not self.current_expression:
                        self.result_text = "Resultado..."
                    else:
                        try:
                            # Prepara a expressão para avaliação
                            expr_to_eval = self._preprocess_expression(self.current_expression)
                            # Usa um dicionário seguro para eval
                            result = eval(expr_to_eval, {"__builtins__": None}, {"math": math})
                            self.result_text = str(result)
                        except Exception as e:
                            self.result_text = f"Erro: {type(e).__name__}"
                
                elif key == b'\x08': # Backspace
                    self.current_expression = self.current_expression[:-1]
                
                elif key == b't': # Parênteses
                    self.current_expression += '(' if not self.parenthesis_open else ')'
                    self.parenthesis_open = not self.parenthesis_open
                
                elif key in self.key_map:
                    self.current_expression += self.key_map[key]

            if click: # Limpar tudo
                self.sound.play_confirm()
                self.current_expression = ""
                self.result_text = "Resultado..."
                self.parenthesis_open = False
                needs_redraw = True

            if direction == 'right': # Sair do app
                self.sound.play_navigation()
                return

            if needs_redraw:
                self.draw_ui()

            time.sleep_ms(20)

# --- Ponto de Entrada do App ---
try:
    app = CalculatorApp(display, touch, trackball, i2c, sound)
    app.run()
except Exception as e:
    print(f"!!! ERRO ao executar Calculadora: {e}")
    _display = globals().get('display')
    if _display:
        _display.fill(st7789.RED)
        _display.text(font, "ERRO NO APP", 10, 10, st7789.WHITE, st7789.RED)
        try:
            _display.text(font, str(e)[:35], 10, 30, st7789.WHITE, st7789.RED)
        except: pass
        time.sleep(5)