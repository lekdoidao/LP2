import tomli
import argparse
import subprocess
import logging
import os
import sys
from datetime import datetime
import time
from pathlib import Path
from multiprocessing import shared_memory
import numpy as np
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
from threading import Thread, Event
import cv2
from utils.setup_routes import _setup_routes
import signal
import psutil

class ImageSaver:
    def __init__(self, config_path: str):
        """
        Inicializa o sistema de salvamento de imagens.
        
        Args:
            config_path: Caminho para o arquivo de configuração TOML
        """
        self.config = self._load_config(config_path)
        self.frame_shape = self.config.get('frame_shape', (1080, 1920, 3))
        self.logger = self._setup_logger()
        self.camera_processes = {}
        self.shared_memories = {}
        self.app = FastAPI()
        self.stop_event = Event()
        
        # Configura rotas da API
        _setup_routes(self.app, self.config, self._generate_frames)

        # Configura handler para sinais de término
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _load_config(self, config_path: str) -> dict:
        """Carrega configurações do arquivo TOML."""
        with open(config_path, 'rb') as f:
            return tomli.load(f)
    
    def _setup_logger(self) -> logging.Logger:
        """Configura o sistema de logging."""
        logger = logging.getLogger('save_images')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        os.makedirs('logs', exist_ok=True)
        fh = logging.FileHandler('logs/save_images.log')
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
    
    def _kill_child_processes(self, parent_pid):
        """Mata todos os processos filhos recursivamente."""
        try:
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            psutil.wait_procs(children, timeout=5)
        except Exception as e:
            self.logger.error(f"Erro ao finalizar processos filhos: {str(e)}")

    def _signal_handler(self, signum, frame):
        """Handler para sinais de término."""
        self.logger.info(f"Sinal {signum} recebido. Iniciando limpeza...")
        self.stop_event.set()
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Realiza limpeza dos recursos."""
        self.logger.info("Iniciando limpeza dos recursos...")
        
        # Finaliza processos das câmeras
        for camera_id, process in self.camera_processes.items():
            try:
                # Mata processo e seus filhos
                self._kill_child_processes(process.pid)
                process.terminate()
                process.wait(timeout=5)
                self.logger.info(f"Processo da câmera {camera_id} finalizado")
            except Exception as e:
                self.logger.error(f"Erro ao finalizar processo da câmera {camera_id}: {str(e)}")
        
        # Limpa memórias compartilhadas
        for camera_id, shm in self.shared_memories.items():
            try:
                shm.close()
                shm.unlink()
                self.logger.info(f"Memória compartilhada {camera_id} liberada")
            except Exception as e:
                self.logger.error(f"Erro ao limpar memória compartilhada {camera_id}: {str(e)}")
    
    def _generate_frames(self, camera_id: str):
        """Gerador de frames para streaming web."""
        while not self.stop_event.is_set():
            try:
                frame = self._get_frame(camera_id)
                if frame is not None:
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(1/self.config.get('web_refresh_rate', 1))
                
            except Exception as e:
                self.logger.error(f"Erro ao gerar frame para {camera_id}: {str(e)}")
                time.sleep(1)
    
    def _get_frame(self, camera_id: str) -> np.ndarray:
        """Obtém o frame mais recente da memória compartilhada."""
        try:
            shm = self.shared_memories.get(camera_id)
            if shm is None:
                return None

            frame = np.ndarray(
                self.frame_shape,
                dtype=np.uint8, 
                buffer=shm.buf
            )
            return frame.copy()
            
        except Exception as e:
            self.logger.error(f"Erro ao obter frame de {camera_id}: {str(e)}")
            return None
    
    def _save_frame(self, camera_id: str, frame: np.ndarray):
        """Salva o frame em disco."""
        try:
            # Cria diretório de saída
            date_str = datetime.now().strftime('%Y-%m-%d')
            time_str = datetime.now().strftime('%H-%M-%S')
            
            # Usa Path para garantir separadores de caminho consistentes
            output_dir = Path(self.config['output_directory']) / camera_id / date_str
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Salva a imagem
            output_path = output_dir / f"{time_str}.jpg"
            cv2.imwrite(str(output_path), frame)
            
            self.logger.info(f"Imagem salva em {output_path}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar frame de {camera_id}: {str(e)}")
    
    def start_camera_processes(self):
        """Inicia os processos de aquisição de imagem para cada câmera."""
        for camera_id, camera_config in self.config['cameras'].items():
            try:
                # Limpa qualquer memória compartilhada existente
                try:
                    shm = shared_memory.SharedMemory(name=camera_id)
                    shm.close()
                    shm.unlink()
                    self.logger.info(f"Memória compartilhada anterior removida: {camera_id}")
                except FileNotFoundError:
                    pass

                # Prepara argumentos para o processo de aquisição
                script_dir = Path(__file__).parent
                exe_path = str(script_dir / "camera_acquisition.exe")
                
                if not Path(exe_path).exists():
                    raise FileNotFoundError(f"Executável não encontrado: {exe_path}")

                cmd = [
                    exe_path,
                    "--camera-url", str(camera_config['url']),
                    "--shared-memory", camera_id,
                    "--frame-rate", str(camera_config.get('frame_rate', 30)),
                    "--retry-interval", str(camera_config.get('retry_interval', 5)),
                    "--frame-shape",
                    str(self.frame_shape[0]),  # altura
                    str(self.frame_shape[1]),  # largura
                    str(self.frame_shape[2])   # canais
]
                
                # Inicia o processo
                self.logger.info(f"Iniciando processo para câmera {camera_id}: {' '.join(cmd)}")
                process = subprocess.Popen(
                    cmd,
                    #stdout=subprocess.PIPE,
                    #stderr=subprocess.PIPE,
                    #text=True,
                    cwd=str(script_dir)
                )
                self.camera_processes[camera_id] = process
                
                # Aguarda a criação da memória compartilhada
                max_retries = 10
                for i in range(max_retries):
                    time.sleep(2)
                    try:
                        self.shared_memories[camera_id] = shared_memory.SharedMemory(name=camera_id)
                        self.logger.info(f"Memória compartilhada conectada para {camera_id}")
                        break
                    except FileNotFoundError:
                        if i == max_retries - 1:
                            self.logger.error(f"Timeout ao conectar à memória compartilhada para {camera_id}")
                    
            except Exception as e:
                self.logger.error(f"Erro ao iniciar processo para {camera_id}: {str(e)}")
    
    def start_saving_thread(self):
        """Inicia thread para salvamento de frames."""
        def saving_loop():
            while not self.stop_event.is_set():
                try:
                    for camera_id, camera_config in self.config['cameras'].items():
                        frame = self._get_frame(camera_id)
                        if frame is not None:
                            self._save_frame(camera_id, frame)
                        
                        time.sleep(camera_config.get('save_interval', 1))
                        
                except Exception as e:
                    self.logger.error(f"Erro no loop de salvamento: {str(e)}")
                    time.sleep(1)
        
        Thread(target=saving_loop, daemon=True).start()
    
    def run(self):
        """Inicia o sistema completo."""
        try:
            # Inicia processos de câmera
            self.start_camera_processes()
            
            # Inicia thread de salvamento
            self.start_saving_thread()
            
            # Inicia servidor web
            uvicorn.run(
                self.app, 
                host="0.0.0.0", 
                port=8888, 
                log_level="info"
            )
            
        finally:
            # Cleanup
            self.cleanup()

def main():
    parser = argparse.ArgumentParser(description='Sistema de Salvamento de Imagens')
    parser.add_argument('--config', default='config.toml', help='Caminho do arquivo de configuração TOML')
    
    args = parser.parse_args()
    
    saver = ImageSaver(args.config)
    saver.run()

if __name__ == "__main__":
    main()