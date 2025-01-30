import cv2
import argparse
import logging
import time
from multiprocessing import shared_memory
import numpy as np
from datetime import datetime
import os
from pathlib import Path

class CameraAcquisition:
    def __init__(self, camera_url: str, shared_memory_name: str, 
                 frame_rate: int = 30, retry_interval: int = 5,
                 frame_shape: tuple = (1080, 1920, 3)):
        """
        Inicializa o sistema de aquisição de imagens.
        
        Args:
            camera_url: URL/path da câmera
            shared_memory_name: Nome do espaço de memória compartilhada
            frame_rate: Taxa de captura desejada
            retry_interval: Intervalo de reconexão em caso de falha
        """
        self.camera_url = camera_url
        self.shared_memory_name = shared_memory_name
        self.frame_rate = frame_rate
        self.retry_interval = retry_interval
        self.frame_shape = frame_shape
        # Configuração do logger
        self.logger = self._setup_logger()
        
        # Inicialização da câmera e memória compartilhada
        self.cap = None
        self.shm = None
    
    def _setup_logger(self) -> logging.Logger:
        """Configura o sistema de logging."""
        logger = logging.getLogger(f'camera_acquisition_{self.shared_memory_name}')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        os.makedirs('logs', exist_ok=True)
        fh = logging.FileHandler(f'logs/camera_acquisition_{self.shared_memory_name}.log')
        fh.setLevel(logging.INFO)
        
        # Handler para console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formato do log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def _connect_camera(self) -> bool:
        try:
            try:
                camera_id = int(self.camera_url)
                self.logger.info(f"Tentando conectar à câmera local {camera_id}")
                self.cap = cv2.VideoCapture(camera_id)
            except ValueError:
                camera_id = self.camera_url
                self.logger.info(f"Tentando conectar à câmera IP {camera_id}")
                # Usa FFMPEG para melhor performance com RTSP
                self.cap = cv2.VideoCapture(camera_id, cv2.CAP_FFMPEG)
            
            # Configura buffer mínimo para reduzir latência
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.cap.isOpened():
                raise Exception("Falha ao abrir a câmera")
            
            # Configura resolução
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_shape[1])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_shape[0])
            
            # Limpa o buffer inicial
            for _ in range(2):
                self.cap.read()
            
            # Adiciona log com a resolução atual
            atual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            atual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.logger.info(f"Câmera conectada com sucesso: {self.camera_url}")
            self.logger.info(f"Resolução configurada: {atual_width}x{atual_height}")
            
            return True
                
        except Exception as e:
            self.logger.error(f"Erro ao conectar câmera: {str(e)}")
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            return False
    
    def _setup_shared_memory(self) -> bool:
        """Configura o espaço de memória compartilhada."""
        try:
            # Calcula o tamanho necessário para o frame
            frame_size = int(np.prod(self.frame_shape) * np.dtype(np.uint8).itemsize)
        
            self.logger.info(f"Criando memória compartilhada com tamanho: {frame_size} bytes")

            # Tenta remover memória compartilhada existente
            try:
                existing_shm = shared_memory.SharedMemory(name=self.shared_memory_name)
                existing_shm.close()
                existing_shm.unlink()
                self.logger.info("Memória compartilhada anterior removida")
            except FileNotFoundError:
                pass
            
            # Cria nova memória compartilhada
            self.shm = shared_memory.SharedMemory(
                name=self.shared_memory_name,
                create=True,
                size=frame_size
            )
            
            self.logger.info(f"Memória compartilhada criada: {self.shared_memory_name} (tamanho: {frame_size})")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar memória compartilhada: {str(e)}")
            return False
    
    def run(self):
        """Loop principal de aquisição de imagens."""
        try:
            while True:
                try:
                    # Tenta conectar à câmera se necessário
                    if self.cap is None or not self.cap.isOpened():
                        if not self._connect_camera():
                            time.sleep(self.retry_interval)
                            continue
                    
                    # Configura memória compartilhada se necessário
                    if self.shm is None:
                        if not self._setup_shared_memory():
                            time.sleep(self.retry_interval)
                            continue
                    
                    # Captura frame
                    ret, frame = self.cap.read()
                    if not ret:
                        raise Exception("Erro ao capturar frame")
                    
                    # Redimensiona o frame para o tamanho padrão
                    frame = cv2.resize(frame, (self.frame_shape[1], self.frame_shape[0]))
                    
                    # Copia frame para memória compartilhada
                    frame_array = np.ndarray(
                        self.frame_shape, 
                        dtype=np.uint8, 
                        buffer=self.shm.buf
                    )
                    frame_array[:] = frame[:]
                    
                    time.sleep(1/self.frame_rate)
                    
                except Exception as e:
                    self.logger.error(f"Erro durante aquisição: {str(e)}")
                    if self.cap is not None:
                        self.cap.release()
                        self.cap = None
                    time.sleep(self.retry_interval)

        except KeyboardInterrupt:
            self.logger.info("Encerrando aquisição de imagens...")
            self._cleanup()
            return
    
    def _cleanup(self):
        """Libera recursos e limpa memória compartilhada."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.shm is not None:
            self.shm.close()
            try:
                self.shm.unlink()
            except FileNotFoundError:
                pass
    
    def __del__(self):
        """Cleanup ao finalizar."""
        self._cleanup()

def main():
    """Sistema de Aquisição de Imagens.
    
    Este programa captura frames de uma câmera e os disponibiliza através de memória compartilhada.
    
    Exemplos de uso:
        # Webcam local:
        python camera_acquisition.py --camera-url 0 --shared-memory cam1
        
        # Câmera IP:
        python camera_acquisition.py --camera-url "rtsp://192.168.1.100:554/stream" --shared-memory cam2
        
        # Ajuste de FPS:
        python camera_acquisition.py --camera-url 0 --shared-memory cam1 --frame-rate 15
    """
    # Configuração dos argumentos de linha de comando
    parser = argparse.ArgumentParser(
        description='Sistema de Aquisição de Imagens',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    # Captura de webcam local:
    %(prog)s --camera-url 0 --shared-memory cam1
    
    # Captura de câmera IP via RTSP:
    %(prog)s --camera-url "rtsp://192.168.1.100:554/stream" --shared-memory cam2
    
    # Ajuste de taxa de captura:
    %(prog)s --camera-url 0 --shared-memory cam1 --frame-rate 15 --retry-interval 3
        """)
    
    parser.add_argument(
        '--camera-url',
        required=True,
        help='URL ou identificador da câmera. Pode ser um número (0, 1, 2...) para webcams locais '
             'ou uma URL (rtsp://, http://) para câmeras IP.'
    )
    
    parser.add_argument(
        '--shared-memory',
        required=True,
        help='Nome do espaço de memória compartilhada onde os frames serão disponibilizados. '
             'Deve ser único para cada câmera.'
    )
    
    parser.add_argument(
        '--frame-rate',
        type=int,
        default=30,
        help='Taxa de captura desejada em frames por segundo (fps). '
             'O valor real pode ser menor dependendo da câmera e do hardware. (default: 30)'
    )
    
    parser.add_argument(
        '--retry-interval',
        type=int,
        default=5,
        help='Intervalo em segundos entre tentativas de reconexão em caso de falha. (default: 5)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Ativa logs de debug para diagnóstico de problemas'
    )

    parser.add_argument(
        '--frame-shape',
        type=int,
        nargs=3,
        default=[1080, 1920, 3],
        help='Resolução do frame no formato "altura largura canais". '
             'Exemplo: 1080 1920 3 para FullHD. (default: 1080 1920 3)'
    )
    args = parser.parse_args()
    
    # Inicia o sistema de aquisição
    acquisition = CameraAcquisition(
        camera_url=args.camera_url,
        shared_memory_name=args.shared_memory,
        frame_rate=args.frame_rate,
        retry_interval=args.retry_interval,
        frame_shape=args.frame_shape
    )
    
    # Configura logging de debug se necessário
    if args.debug:
        acquisition.logger.setLevel(logging.DEBUG)
    
    acquisition.run()

if __name__ == "__main__":
    main()