from pillow_heif import register_heif_opener
from PIL import Image
import os
from pathlib import Path

def converter_heic(pasta_entrada, formato_saida='jpg'):
    """
    Converte todas as imagens HEIC em uma pasta para JPG ou PNG
    
    Args:
        pasta_entrada (str): Caminho da pasta com as imagens HEIC
        formato_saida (str): Formato desejado ('jpg' ou 'png')
    """
    # Registra o decoder HEIF/HEIC
    register_heif_opener()
    
    # Garante que o formato está em minúsculo
    formato_saida = formato_saida.lower()
    if formato_saida not in ['jpg', 'png']:
        raise ValueError("Formato de saída deve ser 'jpg' ou 'png'")
    
    # Cria pasta de saída se não existir
    pasta_saida = os.path.join(pasta_entrada, f'convertidos_{formato_saida}')
    os.makedirs(pasta_saida, exist_ok=True)
    
    # Lista todos os arquivos HEIC
    arquivos_heic = Path(pasta_entrada).glob('*.HEIC')
    arquivos_heic = list(arquivos_heic) + list(Path(pasta_entrada).glob('*.heic'))
    
    for arquivo_heic in arquivos_heic:
        try:
            # Abre a imagem HEIC
            imagem = Image.open(arquivo_heic)
            
            # Define nome do arquivo de saída
            nome_arquivo = arquivo_heic.stem
            arquivo_saida = os.path.join(pasta_saida, f'{nome_arquivo}.{formato_saida}')
            
            # Converte e salva
            if formato_saida == 'jpg':
                imagem.convert('RGB').save(arquivo_saida, 'JPEG')
            else:
                imagem.convert('RGB').save(arquivo_saida, 'PNG')
                
            print(f'Convertido: {arquivo_heic.name} -> {os.path.basename(arquivo_saida)}')
            
        except Exception as e:
            print(f'Erro ao converter {arquivo_heic}: {str(e)}')

if __name__ == '__main__':
    # Exemplo de uso
    pasta = input('Digite o caminho da pasta com as imagens HEIC: ')
    formato = input('Digite o formato desejado (jpg/png): ').lower()
    
    converter_heic(pasta, formato)