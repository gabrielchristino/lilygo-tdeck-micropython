# converter_para_p4.py - Execute este script no seu PC
import os
import struct
from PIL import Image

# Coloque o caminho para a pasta de aplicativos do seu T-Deck
APP_BASE_PATH = '/home/gabriel/Documents/tdeck/teste base/app' # Caminho no seu PC

def convert_to_p4(bmp_path, p4_path):
    """Converte uma imagem para o formato P4 (4-bit com paleta RGB565)."""
    try:
        with Image.open(bmp_path) as img:
            # Garante que a imagem está no modo RGBA para ter canal alfa
            img = img.convert("RGBA")
            
            # Reduz a imagem para uma paleta de 15 cores + 1 cor para transparência
            # O Pillow tentará encontrar as 15 cores mais representativas
            quantized_img = img.quantize(colors=15, method=Image.FASTOCTREE)
            
            # Extrai a paleta ANTES de converter para RGBA
            palette_rgba = quantized_img.getpalette()
            if palette_rgba is None:
                raise ValueError("Não foi possível extrair a paleta da imagem quantizada.")
            # Garante que a paleta tenha 45 bytes (15 cores * 3), preenchendo com 0 se for menor
            palette_rgba.extend([0] * (45 - len(palette_rgba)))

            # Converte a imagem com paleta para RGBA para podermos ler as cores
            quantized_img = quantized_img.convert("RGBA")
            palette_rgb565 = bytearray(32) # 16 cores * 2 bytes/cor
            
            # A cor 0 da nossa paleta será a transparência (preto)
            palette_rgb565[0:2] = struct.pack('>H', 0x0000)

            # Preenche o resto da paleta
            color_map = {}
            for i in range(15):
                r, g, b = palette_rgba[i*3], palette_rgba[i*3+1], palette_rgba[i*3+2]
                
                # Converte para RGB565
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                
                # Armazena em Big Endian para o blit_buffer
                struct.pack_into('>H', palette_rgb565, (i + 1) * 2, rgb565)
                color_map[(r, g, b)] = i + 1

            # Cria os dados de pixel (índices de 4 bits)
            # Obter as dimensões da imagem
            width, height = quantized_img.size
            if (width * height) % 2 != 0:
                raise ValueError(f"A imagem {os.path.basename(bmp_path)} tem um número ímpar de pixels, o que não é suportado.")

            pixel_indices = bytearray(width * height // 2)
            
            pixels = list(quantized_img.getdata())
            
            for i in range(0, len(pixels), 2):
                # Pixel 1
                r1, g1, b1, a1 = pixels[i]
                # Se a cor não for encontrada no mapa (pode acontecer por arredondamento), usa o índice 0 (transparente)
                idx1 = 0 if a1 < 128 else color_map.get((r1, g1, b1), 0) 
                
                # Pixel 2
                r2, g2, b2, a2 = pixels[i+1]
                idx2 = 0 if a2 < 128 else color_map.get((r2, g2, b2), 0) 
                
                # Empacota 2 pixels de 4 bits em 1 byte
                packed_byte = (idx1 << 4) | idx2
                pixel_indices[i // 2] = packed_byte

            # Salva o arquivo .p4 final
            with open(p4_path, 'wb') as f_p4:
                # Escreve a largura e a altura como os dois primeiros bytes
                f_p4.write(bytes([width, height]))
                
                # Escreve a paleta e os dados dos pixels
                f_p4.write(palette_rgb565)
                f_p4.write(pixel_indices)
            
            print(f"  -> Convertido para {os.path.basename(p4_path)}")

    except Exception as e:
        print(f"  -> Falha ao converter {os.path.basename(bmp_path)}: {e}")

# --- Main ---
if __name__ == "__main__":
    if APP_BASE_PATH == '/caminho/para/seu/sd/app':
        print("ERRO: Por favor, edite a variável 'APP_BASE_PATH' no script.")
    else:
        print(f"Iniciando conversão para .p4 em: {APP_BASE_PATH}")
        for dir_name in os.listdir(APP_BASE_PATH):
            app_path = os.path.join(APP_BASE_PATH, dir_name)
            if os.path.isdir(app_path):
                bmp_icon = os.path.join(app_path, '__icon__.bmp')
                p4_icon = os.path.join(app_path, '__icon__.p4')
                if os.path.exists(bmp_icon):
                    print(f"Encontrado ícone em '{dir_name}':")
                    convert_to_p4(bmp_icon, p4_icon)
        print("Conversão concluída.")
