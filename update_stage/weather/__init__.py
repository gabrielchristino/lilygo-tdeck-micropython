# /home/gabriel/Documents/tdeck/teste base/update_stage/weather/__init__.py

import time
import st7789py as st7789
from romfonts import vga1_8x8 as font
import network
import urequests
import json

# --- Constantes ---
BG_COLOR = st7789.color565(15, 25, 40)
TEXT_COLOR = st7789.WHITE
HIGHLIGHT_COLOR = st7789.CYAN
TEMP_COLOR = st7789.WHITE

# --- Configurações da API OpenWeatherMap ---
# !!! SUBSTITUA 'SUA_CHAVE_DE_API_AQUI' PELA SUA CHAVE !!!
API_KEY = "5de1f71c808c69aa34c5edd6c7d66cc9"
CITY_ID = "3448439" # ID para São Paulo, Brasil
BASE_URL = f"http://api.openweathermap.org/data/2.5/weather?id={CITY_ID}&appid={API_KEY}&units=metric&lang=en"

# --- Caminho para as imagens de clima ---
CLIMATE_IMG_DIR = '/sd/app/weather/climate'

class WeatherApp:
    def __init__(self, display, touch, trackball, i2c, sound):
        self.display = display
        self.trackball = trackball
        self.sound = sound
        self.wlan = network.WLAN(network.STA_IF)
        
        self.weather_data = None
        self.error_message = None
        self.focused_button = 'refresh' # 'refresh' ou 'exit'

    def _map_icon(self, icon_code):
        """Mapeia o código do ícone da API para o nome do nosso arquivo de imagem."""
        mapping = {
            "01d": "lv_img_weather_sun.p4",
            "01n": "lv_img_weather_moon.p4",
            "02d": "lv_img_weather_cloud_sun.p4",
            "02n": "lv_img_weather_cloud_moon.p4",
            "03d": "lv_img_weather_cloud.p4",
            "03n": "lv_img_weather_cloud.p4",
            "04d": "lv_img_weather_cloud.p4",
            "04n": "lv_img_weather_cloud.p4",
            "09d": "lv_img_weather_rain.p4",
            "09n": "lv_img_weather_rain.p4",
            "10d": "lv_img_weather_rain.p4",
            "10n": "lv_img_weather_rain.p4",
            "11d": "lv_img_weather_thunderstorm.p4",
            "11n": "lv_img_weather_thunderstorm.p4",
            "13d": "lv_img_weather_snow.p4",
            "13n": "lv_img_weather_snow.p4",
            "50d": "lv_img_weather_mist.p4",
            "50n": "lv_img_weather_mist.p4",
        }
        return mapping.get(icon_code, "lv_img_weather_unknown.p4")

    def _fetch_weather(self):
        """Busca os dados do clima da API."""
        self.weather_data = None
        self.error_message = None
        self.draw_ui("Carregando...")

        if not self.wlan.isconnected():
            self.error_message = "Sem conexao Wi-Fi"
            return

        try:
            response = urequests.get(BASE_URL)
            if response.status_code == 200:
                self.weather_data = response.json()
            else:
                self.error_message = f"Erro API: {response.status_code}"
            response.close()
        except Exception as e:
            self.error_message = "Falha na requisicao"
            print(f"Erro ao buscar clima: {e}")

    def draw_ui(self, status_message=None):
        """Desenha a interface do usuário."""
        self.display.fill(BG_COLOR)
        
        if status_message:
            self.display.text(font, status_message, 20, 100, TEXT_COLOR, BG_COLOR)
        elif self.error_message:
            self.display.text(font, "Erro:", 20, 80, st7789.RED, BG_COLOR)
            self.display.text(font, self.error_message, 20, 100, TEXT_COLOR, BG_COLOR)
        elif self.weather_data:
            # Extrai os dados
            main = self.weather_data.get('main', {})
            weather = self.weather_data.get('weather', [{}])[0]
            
            temp = main.get('temp', '?')
            temp_min = main.get('temp_min', '?')
            temp_max = main.get('temp_max', '?')
            humidity = main.get('humidity', '?')
            description = weather.get('description', 'N/A')
            icon_code = weather.get('icon', '')
            city_name = self.weather_data.get('name', 'N/A')

            # Desenha as informações
            self.display.text(font, city_name, 10, 10, TEXT_COLOR, BG_COLOR)
            
            # Temperatura grande
            temp_str = f"{temp:.0f} C"
            self.display.text(font, temp_str, 140, 60, TEMP_COLOR, BG_COLOR)
            # Desenha o símbolo de grau
            self.display.rect(140 + len(f"{temp:.0f}") * font.WIDTH + 2, 58, 4, 4, TEMP_COLOR)

            # Ícone do clima
            icon_file = self._map_icon(icon_code)
            try:
                # Usa o novo método com transparência!
                self.display.draw_p4_transparent(f"{CLIMATE_IMG_DIR}/{icon_file}", 20, 40)
            except Exception as e:
                print(f"Erro ao desenhar icone {icon_file}: {e}")

            # Outras informações
            self.display.text(font, description, 10, 150, TEXT_COLOR, BG_COLOR)
            
            # --- Desenha Min/Max com símbolo de grau ---
            y_pos = 170
            # Temperatura Mínima
            min_text = f"Min: {temp_min:.0f}"
            self.display.text(font, min_text, 10, y_pos, TEXT_COLOR, BG_COLOR)
            min_degree_x = 10 + len(min_text) * font.WIDTH
            self.display.rect(min_degree_x + 2, y_pos - 2, 3, 3, TEXT_COLOR)
            self.display.text(font, "C", min_degree_x + 6, y_pos, TEXT_COLOR, BG_COLOR)
            # Temperatura Máxima
            max_text = f"Max: {temp_max:.0f}"
            max_text_x = min_degree_x + 20 # Espaçamento
            self.display.text(font, max_text, max_text_x, y_pos, TEXT_COLOR, BG_COLOR)
            max_degree_x = max_text_x + len(max_text) * font.WIDTH
            self.display.rect(max_degree_x + 2, y_pos - 2, 3, 3, TEXT_COLOR)
            self.display.text(font, "C", max_degree_x + 6, y_pos, TEXT_COLOR, BG_COLOR)
            
            self.display.text(font, f"Umidade: {humidity}%", 10, 190, TEXT_COLOR, BG_COLOR)

        # Desenha botões
        refresh_color = HIGHLIGHT_COLOR if self.focused_button == 'refresh' else TEXT_COLOR
        exit_color = HIGHLIGHT_COLOR if self.focused_button == 'exit' else TEXT_COLOR
        self.display.text(font, "[ Atualizar ]", 10, 225, refresh_color, BG_COLOR)
        self.display.text(font, "[ Sair ]", self.display.width - 80, 225, exit_color, BG_COLOR)

    def run(self):
        """Loop principal do aplicativo."""
        self._fetch_weather() # Busca os dados na primeira execução

        while True:
            self.draw_ui()

            # Loop de entrada
            while True:
                direction, click = self.trackball.get_direction()

                if direction in ['left', 'right']:
                    self.focused_button = 'exit' if self.focused_button == 'refresh' else 'refresh'
                    self.sound.play_navigation()
                    break # Quebra para redesenhar o foco

                if click:
                    if self.focused_button == 'refresh':
                        self.sound.play_confirm()
                        self._fetch_weather()
                        break # Quebra para redesenhar com novos dados
                    elif self.focused_button == 'exit':
                        self.sound.play_confirm()
                        return # Fecha o app
                
                time.sleep_ms(50)

# --- Ponto de Entrada do App ---
try:
    app = WeatherApp(display, touch, trackball, i2c, sound)
    app.run()
except Exception as e:
    print(f"!!! ERRO ao executar Weather App: {e}")
    _display = globals().get('display')
    if _display:
        _display.fill(st7789.RED)
        _display.text(font, "ERRO NO APP", 10, 10, st7789.WHITE, st7789.RED)
        try:
            _display.text(font, str(e)[:35], 10, 30, st7789.WHITE, st7789.RED)
        except: pass
        time.sleep(5)
