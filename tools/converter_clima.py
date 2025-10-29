# /home/gabriel/Documents/tdeck/teste base/tools/converter_clima.py

import os
from converter_para_p4 import convert_to_p4 # Reutiliza a função que já temos!

# Caminho para a pasta de imagens de clima no seu PC
CLIMATE_IMG_PATH = '/home/gabriel/Documents/tdeck/teste base/update_stage/weather/climate'

if __name__ == "__main__":
    print(f"Iniciando conversão de imagens de clima em: {CLIMATE_IMG_PATH}")
    if not os.path.exists(CLIMATE_IMG_PATH):
        print(f"ERRO: Diretório não encontrado: {CLIMATE_IMG_PATH}")
    else:
        for filename in os.listdir(CLIMATE_IMG_PATH):
            if filename.endswith('.png'):
                png_path = os.path.join(CLIMATE_IMG_PATH, filename)
                # O nome do arquivo .p4 será o mesmo, mas com a extensão trocada
                p4_path = os.path.join(CLIMATE_IMG_PATH, filename.replace('.png', '.p4'))
                print(f"Convertendo '{filename}'...")
                convert_to_p4(png_path, p4_path)
        print("Conversão de imagens de clima concluída.")
